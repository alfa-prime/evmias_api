#app/core/http_client.py
import json
from typing import Optional, Dict, Any

from httpx import AsyncClient, Response

from app.core.logger import logger


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
            logger.debug(f"ontent-Type '{content_type}' for {url}. JSON parsing skipped")

        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies": dict(response.cookies),
            "content": response.content,
            "text": response.text,
            "json": json_data
        }
        return result

    async def fetch(
            self,
            url: str,
            method: str = "GET",
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] | str = None,
            timeout: Optional[float] = None,
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

        processed_result = self._process_response(response, url)
        return processed_result



