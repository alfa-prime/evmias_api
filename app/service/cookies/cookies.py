from datetime import datetime
from typing import Dict

from app.core import HTTPXClient, get_settings, logger
from fastapi import HTTPException, status

settings = get_settings()


async def fetch_initial_cookies(http_client: HTTPXClient) -> Dict[str, str]:
    """Get first part of cookies."""
    params = {"c": "portal", "m": "promed", "from": "promed" }
    response = await http_client.fetch(
        url = settings.BASE_URL,
        params=params,
        raise_for_status=False,
        follow_redirects=True, # Follow redirects to get the cookies
    )
    status_code = response.get("status_code")
    if status_code != 200:
        logger.error(f"COOKIES: Failed to fetch initial cookies, status code: {status_code}, text: {response}")
        raise HTTPException(
            status_code=status_code,
            detail="Failed to fetch initial cookies"
        )
    logger.info(f"COOKIES: Successfully fetched initial cookies.")
    return response.get("cookies", {})


async def authorize(initial_cookies: Dict[str, str], http_client: HTTPXClient) -> Dict[str, str]:
    """Authorizes the user and adds the login to cookies."""
    logger.debug(f"COOKIES: cookies for authorization: {initial_cookies}")

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

    response = await http_client.fetch(
        url = settings.BASE_URL,
        method="POST",
        cookies=initial_cookies,
        headers=headers,
        params=params,
        data=data,
        raise_for_status=False
    )

    if response['status_code'] != 200 or "true" not in response.get("text", ""):
        logger.error(
            f"COOKIES: Failed to authorize user, "
            f"status code: {response['status_code']}, "
            f"text: {response.get('text', '')}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="COOKIES: Failed to authorize user"
        )

    logger.info("COOKIES: Successfully authorized user.")
    authorized_cookies = initial_cookies.copy()
    authorized_cookies["login"] = settings.EVMIAS_LOGIN

    return authorized_cookies


async def fetch_final_cookies(authorized_cookies: Dict[str, str], http_client: HTTPXClient) -> Dict[str, str]:
    """Retrieves the final part of the cookies via a POST request to the servlet."""
    url = f"{settings.BASE_URL}ermp/servlets/dispatch.servlet"
    headers = {
        "Content-Type": "text/x-gwt-rpc; charset=utf-8",
        "X-Gwt-Permutation": settings.EVMIAS_GWT_PERMUTATION,
        "X-Gwt-Module-Base": "https://evmias.fmba.gov.ru/ermp/",
    }
    data = settings.EVMIAS_GWT

    response = await http_client.fetch(
        url=url,
        method="POST",
        headers=headers,
        cookies=authorized_cookies,
        data=data,
        raise_for_status=False
    )

    if response["status_code"] != 200:
        logger.error(f"COOKIES: failed to fetch final cookies: {response['status_code']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COOKIES: failed to fetch final cookies"
        )

    final_cookies = authorized_cookies.copy()
    logger.info(f"COOKIES: Successfully fetched final cookies.")
    return final_cookies


async def get_new_cookies(http_client: HTTPXClient):
    initial_cookies = await fetch_initial_cookies(http_client)
    authorized_cookies = await authorize(initial_cookies, http_client)
    return authorized_cookies