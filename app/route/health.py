from typing import Annotated

from fastapi import APIRouter, Depends
from app.core import HTTPXClient, get_http_service

router = APIRouter(prefix="/health", tags=["Health check"])


@router.get(path="/ping", summary="PING", description="PONG!")
async def ping():
    return {"success": True, "status": "ok", "message": "PONG!"}



@router.get(path="/client", summary="Check HTTP client", description="Health check")
async def client(http_service: Annotated[HTTPXClient, Depends(get_http_service)]):
    response = await http_service.fetch(url="https://httpbin.org/get")
    return response.get("json")
