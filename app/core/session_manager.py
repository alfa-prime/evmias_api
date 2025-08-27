# app/core/session_manager.py
import json
from typing import Dict, TYPE_CHECKING
from redis.asyncio import Redis
from app.core.logger_config import logger
from app.service import perform_re_authentication

if TYPE_CHECKING:
    from app.core.http_client import HTTPXClient


class SessionManager:
    def __init__(self, redis_client: Redis, cookies_key: str, ttl: int):
        self.redis = redis_client
        self.cookies_key = cookies_key
        self.ttl = ttl
        self.lock_key = f"{cookies_key}:lock"

    async def get_cookies(self) -> Dict[str, str] | None:
        """Получает cookie из Redis."""
        json_cookies = await self.redis.get(self.cookies_key)
        if not json_cookies:
            logger.info("[SESSION] Cookies not found in Redis.")
            return None
        logger.debug("[SESSION] Cookies successfully retrieved from Redis.")
        return json.loads(json_cookies)

    async def save_cookies(self, cookies: Dict[str, str]) -> None:
        """Сохраняет cookie в Redis с установкой времени жизни."""
        json_cookies = json.dumps(cookies)
        await self.redis.set(self.cookies_key, json_cookies, ex=self.ttl)
        logger.info(f"[SESSION] Cookies saved to Redis with TTL {self.ttl}s.")

    async def re_authenticate(self, http_client: "HTTPXClient") -> Dict[str, str]:
        logger.warning("[SESSION] Re-authentication process started.")
        async with self.redis.lock(self.lock_key, timeout=60):
            logger.info("[SESSION] Acquired distributed lock for re-authentication.")
            cookies = await self.get_cookies()
            if cookies:
                logger.info("[SESSION] Cookies were updated by another process. Using fresh cookies.")
                return cookies
            logger.info("[SESSION] Performing re-authentication against EVMIAS.")
            new_cookies = await perform_re_authentication(http_client)
            await self.save_cookies(new_cookies)
            logger.info("[SESSION] Re-authentication successful. New cookies stored.")
            return new_cookies