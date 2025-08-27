from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BASE_URL: str
    BASE_HEADERS_ORIGIN_URL: str
    BASE_HEADERS_REFERER_URL: str

    EVMIAS_LOGIN: str
    EVMIAS_PASSWORD: str

    LOGS_LEVEL: str = "INFO"
    DEBUG_HTTP: bool = False
    DEBUG_ROUTE: bool = False

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_COOKIES_KEY: str
    REDIS_COOKIES_TTL: int

    GATEWAY_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings() # noqa
