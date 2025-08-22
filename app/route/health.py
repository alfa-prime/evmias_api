from typing import Annotated

from fastapi import APIRouter, Depends

from app.core import HTTPXClient, get_http_service, get_settings

router = APIRouter(prefix="/health", tags=["Health check"])

settings = get_settings()


@router.get(path="/ping", summary="PING", description="PONG!")
async def ping():
    return {"success": True, "status": "ok", "message": "PONG!"}


@router.get(path="/client", summary="Check HTTP client", description="Health check")
async def client(http_service: Annotated[HTTPXClient, Depends(get_http_service)]):
    response = await http_service.fetch(url="https://httpbin.org/get")
    return response.get("json")


# ======================= testing area =======================
@router.get(path="/test")
async def test(http_service: Annotated[HTTPXClient, Depends(get_http_service)]):
    params = {"c": "Common", "m": "getCurrentDateTime"}
    data = {"is_activerules": "true"}

    response = await http_service.fetch(
        url=settings.BASE_URL,
        method="POST",
        params=params,
        data=data,
        raise_for_status=False
    )
    return response
