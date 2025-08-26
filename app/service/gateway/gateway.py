#app/service/proxy/proxy.py
from app.core import HTTPXClient
from app.model import GatewayRequest


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
    return response