from .health import router as health_router
from .proxy import router as proxy_router

__all__ = [
    "proxy_router",
    "health_router",
]