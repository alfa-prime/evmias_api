#app/service/auth/auth.py
from app.core import HTTPXClient, get_settings
from app.core.logger_config import logger
from fastapi import HTTPException, status

settings = get_settings()


async def warmup_session_and_fetch_initial_cookies(http_client: HTTPXClient) -> None:
    """Get first part of cookies."""
    params = {"c": "portal", "m": "promed", "from": "promed" }
    response = await http_client._execute_fetch( # noqa
        url = settings.BASE_URL,
        params=params,
        raise_for_status=False,
        follow_redirects=True, # Follow redirects to get the cookies
    )
    status_code = response.get("status_code")
    if status_code != 200:
        logger.error(f"[AUTH] Failed to fetch initial cookies, status code: {status_code}, text: {response}")
        raise HTTPException(
            status_code=status_code,
            detail="Failed to fetch initial cookies"
        )
    logger.info(f"[AUTH] Successfully fetched initial cookies.")


async def authorize_session(http_client: HTTPXClient) -> None:
    """Authorizes the user and adds the login to cookies."""
    headers = {
        "Origin": settings.BASE_HEADERS_ORIGIN_URL,
        "Referer": settings.BASE_HEADERS_REFERER_URL,
        "X-Requested-With": "XMLHttpRequest",
    }

    params = {
        "c": "main",
        "m": "index",
        "method": "Logon",
        "login": settings.EVMIAS_LOGIN
    }

    data = {
        "login": settings.EVMIAS_LOGIN,
        "psw": settings.EVMIAS_PASSWORD,
        "swUserRegion": "",
        "swUserDBType": "",
    }

    response = await http_client._execute_fetch( # noqa
        url = settings.BASE_URL,
        method="POST",
        headers=headers,
        params=params,
        data=data,
        raise_for_status=False
    )

    if response['status_code'] != 200 or "true" not in response.get("text", ""):
        logger.error(
            f"[AUTH] Failed to authorize user, "
            f"status code: {response['status_code']}, "
            f"text: {response.get('text', '')}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="[AUTH] Failed to authorize user"
        )

    logger.info("[AUTH] Successfully authorized user.")


async def perform_re_authentication(http_client: HTTPXClient):
    await warmup_session_and_fetch_initial_cookies(http_client)
    await authorize_session(http_client)

