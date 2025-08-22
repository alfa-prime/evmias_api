# app/core/dependencies.py
from fastapi import Request

from app.core import HTTPXClient
from app.service import perform_re_authentication


async def get_http_service(request: Request) -> HTTPXClient:
    base_client = request.app.state.http_client
    auth_lock = request.app.state.auth_lock
    return HTTPXClient(
        client=base_client,
        auth_lock=auth_lock,
        reauth_func=perform_re_authentication
    )
