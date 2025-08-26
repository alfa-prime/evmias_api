# app/route/gateway.py
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core import HTTPXClient, get_http_service, route_handler ,get_settings
from app.model.gateway import GatewayRequest
from app.service import fetch_request


settings = get_settings()
router = APIRouter(prefix="/gateway", tags=["EVMIAS gateway"])

@route_handler(debug=settings.DEBUG_ROUTE)
@router.post(
    path="/",
    summary="Выполнить запрос к ЕВМИАС и вернуть чистый JSON",
    description="""
    Принимает описание запроса и выполняет его к API ЕВМИАС.

    - В случае успеха возвращает JSON-ответ от ЕВМИАС.
    - В случае, если от ЕВМИАС не удалось получить валидный JSON 
      (например, из-за ошибки сессии), возвращает ошибку 502 Bad Gateway.

    Дальнейшая обработка ошибок бизнес-логики (например, "пациент не найден")
    остается на стороне клиента, вызывающего этот эндпоинт.
    """
)
async def request(
        payload: GatewayRequest,
        http_service: Annotated[HTTPXClient, Depends(get_http_service)]
) -> Any:
    # Просто вызываем сервис и возвращаем то, что он отдал.
    # Если fetch_request вызовет HTTPException, FastAPI его перехватит
    # и вернет клиенту корректный ответ с ошибкой.
    json_response = await fetch_request(payload, http_service)
    return json_response
