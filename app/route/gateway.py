#app/route/proxy.py
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core import HTTPXClient, get_http_service
from app.model.gateway import GatewayRequest
from app.service import fetch_request

router = APIRouter(prefix="/gateway", tags=["EVMIAS gateway"])


@router.post(path="/")
async def request(
        payload: GatewayRequest,
        http_service: Annotated[HTTPXClient, Depends(get_http_service)]
):
    response = await fetch_request(payload, http_service)
    return response
