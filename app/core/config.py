from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BASE_URL: str
    BASE_HEADERS_ORIGIN_URL: str
    BASE_HEADERS_REFERER_URL: str

    EVMIAS_LOGIN: str
    EVMIAS_PASSWORD: str

    EVMIAS_GWT_PERMUTATION: str
    EVMIAS_GWT: str
    EVMIAS_GWT_MODULE_BASE: str

    LOGS_LEVEL: str = "INFO"
    DEBUG_HTTP: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings() # noqa
