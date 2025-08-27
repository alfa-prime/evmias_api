# main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import (
    logger,
    init_httpx_client,
    shutdown_httpx_client,
)
from app.route import gateway_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    logger.info("Starting application...")
    await init_httpx_client(app)
    logger.info("Initialization completed.")
    yield
    logger.info("Shutting down application...")
    await shutdown_httpx_client(app)
    logger.info("Resources released.")


app = FastAPI(
    lifespan=lifespan,
    title="E-Gate: API Gateway for EVMIAS",
    description="""
    API-шлюз для запросов к ЕВМИАС API.

    Основные возможности:
    *   Автоматическое управление сессией: Сервис самостоятельно выполняет аутентификацию и поддерживает сессию активной.
    *   Универсальный шлюз: Позволяет выполнять произвольные запросы к API ЕВМИАС через единый эндпоинт `/gateway/request`.
    *   Централизованное логирование и обработка ошибок.
    """,
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gateway_router)
