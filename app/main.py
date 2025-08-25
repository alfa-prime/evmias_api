#main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core import (
    logger,
    init_httpx_client,
    shutdown_httpx_client,
)
from app.route import health_router, proxy_router

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    logger.info("Starting application...")
    await init_httpx_client(app)
    logger.info("Initialization completed.")
    yield
    logger.info("Shutting down application...")
    await shutdown_httpx_client(app)
    logger.info("Resources released.")


tags_metadata = [
    {"name": "Health check", "description": "checks if the service is running"},
    {
        "name": "EVMIAS proxy",
        "description": "🚀 Универсальный шлюз для запросов к EVMIAS API",
    },
]

app = FastAPI(
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    title="MIS Synchronization API",
    description="""
    API-шлюз для синхронизации медицинских данных между ЕВМИАС и другими МИС.

    Основные возможности:
    *   Автоматическое управление сессией: Сервис самостоятельно выполняет аутентификацию и поддерживает сессию активной.
    *   Универсальный прокси: Позволяет выполнять произвольные запросы к API ЕВМИАС через единый эндпоинт `/proxy/`.
    *   Централизованное логирование и обработка ошибок.
    """,
)
app.include_router(proxy_router)
app.include_router(health_router)



