from .http_client import HTTPXClient
from .config import get_settings
from .dependencies import get_http_service
from .lifespan import init_httpx_client, shutdown_httpx_client
from .logger_config import logger

__all__ = [
    "logger",
    "HTTPXClient",
    "init_httpx_client",
    "shutdown_httpx_client",
    "get_http_service",
    "get_settings",
]
