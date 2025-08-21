#app/core/http_client.py
import json
from typing import Optional, Dict, Any

from httpx import AsyncClient, Response, HTTPStatusError, RequestError, TimeoutException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.core.logger_config import logger
from app.core.config import get_settings
from app.core.decorators import log_and_catch

settings = get_settings()


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
    def __init__(self, client: AsyncClient):
        self.client = client

    def _process_response(self, response: Response, url: str) -> dict: # noqa
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

        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies": dict(response.cookies),
            "content": response.content,
            "text": response.text,
            "json": json_data
        }
        return result

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_exception),  # Используем фильтр
        retry_error_callback=lambda retry_state: logger.error(
            f"[HTTPX] Attempt limit exceeded "
            f"({retry_state.attempt_number}) for {retry_state.args[1] if len(retry_state.args) > 1 else 'URL?'} "
            f"after error: {retry_state.outcome.exception()}"),
        before_sleep=lambda r: logger.warning(
            f"[HTTPX] Attempt {r.attempt_number} for {r.args[1] if len(r.args) > 1 else 'URL?'} "
            f"failed due to {type(r.outcome.exception()).__name__} - {r.outcome.exception()}"
        )
    )
    @log_and_catch(debug=settings.DEBUG_HTTP)
    async def fetch(
            self,
            url: str,
            method: str = "GET",
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] | str = None,
            timeout: Optional[float] = None,
            raise_for_status: bool = True,

            **kwargs
    ) -> Dict[str, Any]:
        request_timeout = timeout if timeout is not None else 30.0

        response: Response = await self.client.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            timeout=request_timeout,
            **kwargs
        )

        if raise_for_status:
            try:
                response.raise_for_status()
            except HTTPStatusError as http_error:
                # Логируем 4xx/5xx ошибки, но пробрасываем дальше для retry
                logger.warning(f"[HTTPX] Response status {http_error.response.status_code} for {url}.")
                raise http_error

        processed_result = self._process_response(response, url)
        return processed_result



