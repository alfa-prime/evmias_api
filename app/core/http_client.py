# app/core/http_client.py
import asyncio
import json
from typing import Dict, Any, Callable, Awaitable

from httpx import AsyncClient, Response, HTTPStatusError, RequestError, TimeoutException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.core.config import get_settings
from app.core.decorators import log_and_catch
from app.core.logger_config import logger

settings = get_settings()


# def _is_auth_error(response: Dict[str, Any]) -> bool:
#     """Определяет, является ли ответ ошибкой авторизации."""
#     status_code = response.get("status_code")
#
#     if status_code in (401, 403):
#         logger.warning(f"[AUTH] Explicit authorization error detected (status: {status_code}).")
#         return True
#
#     if status_code == 200:
#         response_json = response.get("json")
#         if not response_json:
#             logger.warning("[AUTH] Detected 200 OK with empty or missing JSON, signaling an expired session.")
#             return True
#
#     return False


def _is_retryable_exception(exception) -> bool:
    """Определяет, стоит ли повторять запрос при этой ошибке."""
    # Повторяем при ошибках сети/сервера/таймаута/статуса 5xx
    # Не повторяем при 4xx, т.к. они обычно требуют исправления запроса
    if isinstance(exception, HTTPStatusError):
        return 500 <= exception.response.status_code < 600
    return isinstance(exception, (
        RequestError,
        TimeoutException
    ))


class HTTPXClient:
    def __init__(
            self, client: AsyncClient, auth_lock: asyncio.Lock,
            reauth_func: Callable[['HTTPXClient'], Awaitable[Any]]
    ):
        self.client = client
        self.auth_lock = auth_lock
        self.reauth_func = reauth_func

    def _is_auth_error(self, response: Dict[str, Any]) -> bool: # noqa
        """Определяет, является ли ответ ошибкой авторизации."""
        status_code = response.get("status_code")

        if status_code in (401, 403):
            logger.warning(f"[HTTPX] Explicit authorization error detected (status: {status_code}).")
            return True

        if status_code == 200:
            response_json = response.get("json")
            if not response_json:
                logger.warning("[HTTPX] Detected 200 OK with empty or missing JSON, signaling an expired session.")
                return True

        return False

    def _process_response(self, response: Response, url: str) -> dict:  # noqa
        json_data = None
        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            try:
                if response.content:
                    json_data = response.json()
                    logger.debug(f"Successfully parsed JSON (application/json) response for {url}")
                else:
                    logger.debug(f"Content-Type 'application/json', but response body is empty for {url}")
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to decode JSON (application/json) from response {url}: {e}. Text: {response.text[:200]}...")

        elif "text/html" in content_type:
            if response.text:
                try:
                    json_data = json.loads(response.text)
                    logger.debug(f"Successfully parsed JSON (из text/html) response for {url}")
                except json.JSONDecodeError:
                    logger.debug(f"Content-Type 'text/html' for {url}, but response body is not valid JSON.")
            else:
                logger.debug(f"Content-Type 'text/html' for {url}, but response body is empty.")
        else:
            logger.debug(f"Content-Type '{content_type}' for {url}. JSON parsing skipped")

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies": dict(response.cookies),
            "content": response.content,
            "text": response.text,
            "json": json_data
        }

    @log_and_catch(debug=settings.DEBUG_HTTP)
    async def fetch(
            self,
            url: str,
            method: str = "GET",
            raise_for_status: bool = True,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Главный метод-оркестратор. Выполняет запрос, обрабатывая ошибки
        авторизации и автоматически выполняя повторный вход в систему.
        """
        # Первая попытка
        follow_redirects = kwargs.pop('follow_redirects', False)

        response_dict = await self._execute_fetch(
            url=url,
            method=method,
            raise_for_status=raise_for_status,
            follow_redirects=follow_redirects,
            **kwargs
        )

        # Если это не ошибка авторизации, все хорошо, возвращаем результат
        if not self._is_auth_error(response_dict):
            return response_dict

        logger.warning(f"[HTTPX] Authorization error detected for {method} {url}. Attempting re-authentication.")

        async with self.auth_lock:
            logger.info("[HTTPX] Acquired auth lock. Proceeding with re-authentication.")
            await self.reauth_func(self)
            logger.info("[HTTPX] Re-authentication successful.")

        logger.info(f"[HTTPX] Retrying original request to {method} {url}.")
        # Вторая и последняя попытка после переавторизации
        final_response_dict = await self._execute_fetch(
            url=url, method=method, raise_for_status=raise_for_status, **kwargs
        )

        return final_response_dict

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_exception),
        retry_error_callback=lambda retry_state: logger.error(
            f"[HTTPX] Attempt limit exceeded after error: {retry_state.outcome.exception()}"),
        before_sleep=lambda r: logger.warning(
            f"[HTTPX] Attempt {r.attempt_number} failed due to {r.outcome.exception()}")
    )
    async def _execute_fetch(
            self,
            raise_for_status: bool,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Приватный метод-исполнитель. Выполняет один HTTP-запрос,
        обрабатывает ответ и сетевые ошибки (с помощью Tenacity).
        """
        # Извлекаем специфичные для fetch аргументы из kwargs, чтобы передать их явно
        method = kwargs.pop('method', 'GET')
        url = kwargs.pop('url')

        # Мы отключаем `raise_for_status` на уровне httpx, чтобы наша логика
        # в `fetch` могла увидеть ответ 401 и принять решение.
        response: Response = await self.client.request(
            method=method,
            url=url,
            timeout=30.0,
            **kwargs
        )

        processed_result = self._process_response(response, url)

        # Если это НЕ ошибка авторизации, НО это другая ошибка (404, 500),
        # и вызывающий код просил возбудить исключение, мы делаем это вручную.
        if raise_for_status and not self._is_auth_error(processed_result) and response.status_code >= 400:
            response.raise_for_status()

        return processed_result
