from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core import HTTPXClient, get_http_service
from app.model.proxy import ProxyRequest

router = APIRouter(prefix="/proxy", tags=["EVMIAS proxy"])


@router.post(path="/")
async def test(
        payload: ProxyRequest,
        http_service: Annotated[HTTPXClient, Depends(get_http_service)]
):
    response = await http_service.fetch(
        url=payload.path,
        method=payload.method,
        params=payload.params.model_dump(),
        data=payload.data,
        raise_for_status=False
    )
    return {
        "response_status_code": response.get("status_code"),
        "response_headers": response.get("headers"),
        "response_json": response.get("json", None),
        "response_content": response.get("content", None),
        "response_text": response.get("text", None),
    }
