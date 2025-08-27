# app/core/dependencies.py
from fastapi import Request, Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core import HTTPXClient, get_settings
from app.service import perform_re_authentication


async def get_http_service(request: Request) -> HTTPXClient:
    base_client = request.app.state.http_client
    auth_lock = request.app.state.auth_lock
    return HTTPXClient(
        client=base_client,
        auth_lock=auth_lock,
        reauth_func=perform_re_authentication
    )



api_key_header = APIKeyHeader(name="X-API-KEY")
settings = get_settings()

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == settings.GATEWAY_API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is missing or invalid",

        )