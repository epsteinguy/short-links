from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./shortener.db"
    SECRET_KEY: str = "CHANGE_ME_IN_ENV"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 48
    BASE_URL: str = "http://localhost:8080"
    CORS_ORIGINS: str = "*"
    ADMIN_BOOTSTRAP_TOKEN: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings():
    return Settings()
