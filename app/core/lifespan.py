#app/core/lifespan.py
import asyncio

import httpx
from fastapi import FastAPI
from app.core.logger_config import logger
from app.core import get_settings




async def init_httpx_client(app: FastAPI):
    settings = get_settings()

    base_headers = {
        "Origin": settings.BASE_HEADERS_ORIGIN_URL,
        "Referer": settings.BASE_HEADERS_REFERER_URL,
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        base_client = httpx.AsyncClient(
            base_url=settings.BASE_URL,
            headers=base_headers,
            timeout=30.0,
            verify=False  # TODO: убрать verify=False
        )
        app.state.http_client = base_client
        app.state.auth_lock = asyncio.Lock()
        logger.info("Base HTTPX client and auth lock initialized.")
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize HTTPX client: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize HTTPX client: {e}")


async def shutdown_httpx_client(app: FastAPI):
    if hasattr(app.state, 'http_client') and app.state.http_client:
        try:
            await app.state.http_client.aclose()
            logger.info("Base HTTPX client is closed")
        except Exception as e:
            logger.error(f"Base HTTPX client is closed: {e}", exc_info=True)