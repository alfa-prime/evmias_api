# app/service/auth/auth.py
from typing import Dict
from app.core.config import get_settings
from app.core.logger_config import logger
from fastapi import HTTPException
from httpx import Cookies, AsyncClient

settings = get_settings()

async def warmup_session_and_fetch_initial_cookies(http_client: AsyncClient) -> Cookies:
    """Получает первую часть cookie, используя 'чистый' http клиент."""
    params = {"c": "portal", "m": "promed", "from": "promed"}
    response = await http_client.get("/", params=params, follow_redirects=True)
    if response.status_code != 200:
        logger.error(f"[AUTH] Failed to fetch initial cookies, status: {response.status_code}, text: {response.text}")
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch initial cookies")
    logger.info("[AUTH] Successfully fetched initial cookies.")
    return response.cookies

async def authorize_session(http_client: AsyncClient, cookies: Cookies) -> Cookies:
    """Авторизует сессию и возвращает финальный набор cookie."""
    params = {"c": "main", "m": "index", "method": "Logon", "login": settings.EVMIAS_LOGIN}
    data = {"login": settings.EVMIAS_LOGIN, "psw": settings.EVMIAS_PASSWORD, "swUserRegion": "", "swUserDBType": ""}
    response = await http_client.post("/", params=params, data=data, cookies=cookies, follow_redirects=False)
    if response.status_code != 200 or "true" not in response.text:
        logger.error(f"[AUTH] Failed to authorize user, status: {response.status_code}, text: {response.text}")
        raise HTTPException(status_code=response.status_code, detail="[AUTH] Failed to authorize user")
    logger.info("[AUTH] Successfully authorized user.")
    cookies.update(response.cookies)
    return cookies

async def perform_re_authentication(http_client_instance) -> Dict[str, str]:
    """
    Оркестрирует процесс переаутентификации.
    Принимает экземпляр нашего HTTPXClient, чтобы использовать его 'чистый' базовый http-клиент.
    """
    # Используем базовый httpx.AsyncClient для аутентификации, чтобы избежать рекурсивных вызовов fetch()
    clean_http_client = http_client_instance.client
    initial_cookies = await warmup_session_and_fetch_initial_cookies(clean_http_client)
    final_cookies = await authorize_session(clean_http_client, initial_cookies)
    return dict(final_cookies)