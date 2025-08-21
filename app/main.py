#main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core import (
    logger,
    init_httpx_client,
    shutdown_httpx_client,
)
from app.route import (
    health_router,
)

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
]

app = FastAPI(
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    title="MIS Synchronization API",
    description="API gateway for extracting and synchronizing medical data from EVMIAS to other MIS.",
)
app.include_router(health_router)


