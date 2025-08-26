# app/service/proxy/proxy.py
from fastapi import HTTPException

from app.core import HTTPXClient, log_and_catch, get_settings
from app.model import GatewayRequest

settings = get_settings()


@log_and_catch(debug=settings.DEBUG_HTTP)
async def fetch_request(
        payload: GatewayRequest,
        http_client: HTTPXClient
):
    response = await http_client.fetch(
        url=payload.path,
        method=payload.method,
        params=payload.params.model_dump(),
        data=payload.data,
        raise_for_status=False
    )

    response_json = response.get("json")

    if not response_json:
        # Это единственная ошибка, за которую отвечает этот слой.
        # Она означает "Не удалось установить связь и получить данные".
        raise HTTPException(
            status_code=502,  # Bad Gateway: "Мы, как шлюз, не смогли получить ответ от сервера за нами"
            detail={
                "error": "Failed to get a valid JSON response from EVMIAS",
                "upstream_status_code": response.get("status_code"),
                "upstream_response_text": response.get("text")
            }
        )

    return response_json
