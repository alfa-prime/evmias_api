# app/core/http_client.py
import json
from typing import Dict, Any

from httpx import AsyncClient, Response, HTTPStatusError, RequestError, TimeoutException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.core.config import get_settings
from app.core.decorators import log_and_catch
from app.core.logger_config import logger
from app.core.session_manager import SessionManager  # Импортируем SessionManager

settings = get_settings()


def _is_retryable_exception(exception) -> bool:
    if isinstance(exception, HTTPStatusError):
        return 500 <= exception.response.status_code < 600
    return isinstance(exception, (RequestError, TimeoutException))


class HTTPXClient:
    # Конструктор теперь принимает session_manager вместо lock и reauth_func
    def __init__(self, client: AsyncClient, session_manager: SessionManager):
        self.client = client
        self.session_manager = session_manager

    def _is_auth_error(self, response: Dict[str, Any]) -> bool: # noqa
        status_code = response.get("status_code")
        if status_code in (401, 403):
            logger.warning(f"[HTTPX] Explicit authorization error detected (status: {status_code}).")
            return True
        if status_code == 200 and not response.get("json"):
            logger.warning("[HTTPX] Detected 200 OK with empty or missing JSON, signaling an expired session.")
            return True
        return False

    def _process_response(self, response: Response, url: str) -> dict: # noqa
        json_data = None
        content_type = response.headers.get("Content-Type", "").lower()
        try:
            if "application/json" in content_type and response.content:
                json_data = response.json()
            elif "text/html" in content_type and response.content:
                json_data = json.loads(response.text)
        except json.JSONDecodeError:
            logger.debug(f"[HTTPX] Content-Type '{content_type}' for {url}, but response body is not valid JSON.")

        return {
            "status_code": response.status_code, "headers": dict(response.headers),
            "cookies": dict(response.cookies), "content": response.content,
            "text": response.text, "json": json_data
        }

    @log_and_catch(debug=settings.DEBUG_HTTP)
    async def fetch(
            self, url: str = "/", method: str = "GET", raise_for_status: bool = True, **kwargs
    ) -> Dict[str, Any]:
        """
        Главный метод-оркестратор. Получает сессию из Redis, выполняет запрос
        и обрабатывает ошибки авторизации, запуская переаутентификацию.
        """
        cookies = await self.session_manager.get_cookies()

        # Первая попытка с текущими cookie (или без них)
        response_dict = await self._execute_fetch(
            url=url, method=method, raise_for_status=raise_for_status, cookies=cookies, **kwargs
        )

        # Если все хорошо, возвращаем результат
        if not self._is_auth_error(response_dict):
            return response_dict

        logger.warning(f"[HTTPX] Authorization error for {method} {url}. Attempting re-authentication.")

        # Запускаем переаутентификацию через SessionManager
        final_cookies = await self.session_manager.re_authenticate(self)

        logger.info(f"[HTTPX] Retrying original request to {method} {url} with fresh cookies.")
        # Вторая и последняя попытка с новыми cookie
        final_response_dict = await self._execute_fetch(
            url=url, method=method, raise_for_status=raise_for_status, cookies=final_cookies, **kwargs
        )

        return final_response_dict

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_exception),
        retry_error_callback=lambda rs: logger.error(f"[HTTPX] Attempt limit exceeded: {rs.outcome.exception()}"),
        before_sleep=lambda r: logger.warning(f"[HTTPX] Attempt {r.attempt_number} failed: {r.outcome.exception()}")
    )
    async def _execute_fetch(self, url: str, method: str, raise_for_status: bool, **kwargs) -> Dict[str, Any]:
        """Приватный метод-исполнитель. Выполняет один HTTP-запрос."""
        response = await self.client.request(method=method, url=url, timeout=30.0, **kwargs)
        processed_result = self._process_response(response, url)

        if raise_for_status and not self._is_auth_error(processed_result) and response.status_code >= 400:
            response.raise_for_status()

        return processed_result