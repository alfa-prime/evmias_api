# app/core/dependencies.py
from typing import Optional

from fastapi import Request, HTTPException, status, Header, Security
from fastapi.security import APIKeyHeader

from app.core import get_settings, HTTPXClient
from app.core.session_manager import SessionManager

settings = get_settings()


async def get_http_service(request: Request) -> HTTPXClient:
    """
    Dependency-функция, которая 'собирает' и предоставляет HTTPXClient для обработчиков роутов.
    """
    base_client = request.app.state.http_client
    redis_client = request.app.state.redis_client

    # Создаем SessionManager, передавая ему параметры из конфига
    session_manager = SessionManager(
        redis_client=redis_client,
        cookies_key=settings.REDIS_COOKIES_KEY,
        ttl=settings.REDIS_COOKIES_TTL
    )

    # Создаем и возвращаем наш новый stateless HTTPXClient
    return HTTPXClient(
        client=base_client,
        session_manager=session_manager
    )

api_key_header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key: Optional[str] = Security(api_key_header_scheme)):
    """
    Проверяет X-API-KEY. Теперь эта функция полностью контролирует ответ об ошибке.
    """
    if api_key and api_key == settings.GATEWAY_API_KEY:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "Authentication Failed",
            "message": "The provided X-API-KEY is missing or invalid.",
            "remedy": "Please include a valid 'X-API-KEY' header in your request."
        },
    )
