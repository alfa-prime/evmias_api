from typing import Literal, Optional, Dict, Any

from pydantic import BaseModel, Field


class RequestParams(BaseModel):
    c: str = Field(..., description="Имя контроллера в API ЕВМИАС.", examples=["Common"])
    m: str = Field(..., description="Имя вызываемого метода в контроллере.", examples=["getCurrentDateTime"])


class GatewayRequest(BaseModel):
    """
    Model for gateway request for EVMIAS api
    """
    path: str = Field(
        default="/",
        description="Путь запроса относительно базового URL. В 99% случаев это будет '/'",
        examples=["/"]
    )

    method: Literal["GET", "POST"] = Field(
        default="POST",
        description="HTTP-метод, который будет использован для запроса к ЕВМИАС.",
        examples=["POST"]
    )

    params: RequestParams

    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Тело запроса (payload) для POST-запросов.",
        examples=[{"is_activerules": "true"}]
    )
