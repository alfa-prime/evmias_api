#app/core/dependencies.py
from fastapi import Request

from app.core import HTTPXClient


async def get_http_service(request: Request) -> HTTPXClient:
    base_client = request.app.state.http_client
    return HTTPXClient(client=base_client)
