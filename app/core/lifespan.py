# app/core/lifespan.py
import asyncio

import httpx
import redis.asyncio as redis
from fastapi import FastAPI

from app.core import get_settings
from app.core.logger_config import logger

settings = get_settings()


async def init_httpx_client(app: FastAPI):
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
        # app.state.auth_lock = asyncio.Lock()  !!!!!
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


async def init_redis_client(app: FastAPI):
    """Инициализирует и сохраняет Redis клиент в app.state. При ошибке приложение падает и не стартует."""
    try:
        redis_pool = redis.ConnectionPool.from_url(
            url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            decode_responses=True,
            max_connections=10
        )
        redis_client = redis.Redis(connection_pool=redis_pool)
        await redis_client.ping()  # Проверка соединения
        app.state.redis_client = redis_client
        logger.info(
            f"Redis client connected to {settings.REDIS_HOST}:{settings.REDIS_PORT}"
        )
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to connect to Redis: {e}", exc_info=True)
        raise RuntimeError(f"Failed to connect to Redis: {e}")


async def shutdown_redis_client(app: FastAPI):
    """Закрывает Redis клиент."""
    if hasattr(app.state, 'redis_client') and app.state.redis_client:
        try:
            await app.state.redis_client.close()
            logger.info("Redis client is closed")
        except Exception as e:
            logger.error(f"Error close Redis client: {e}", exc_info=True)
