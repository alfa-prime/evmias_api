#main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import (
    logger,
    init_httpx_client,
    shutdown_httpx_client,
)
from app.route import health_router, gateway_router

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
        "name": "EVMIAS gateway",
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


origins = ["*"]

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Разрешить все методы (GET, POST и т.д.)
    allow_headers=["*"], # Разрешить все заголовки
)

app.include_router(gateway_router)
app.include_router(health_router)



