#app/core/lifespan.py
import httpx
from fastapi import FastAPI
from app.core.logger_config import logger


async def init_httpx_client(app: FastAPI):
    try:
        base_client = httpx.AsyncClient(
            timeout=30.0,
            verify=False,  # TODO: убрать verify=False
        )
        app.state.http_client = base_client
        logger.info("Base HTTPX client initialized and stored in app.state")
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