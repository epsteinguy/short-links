from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./shortener.db"

    SECRET_KEY: str = "thisisanurlshortner"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 48
    # 48 Hours / 2 Days expiration for now
    BASE_URL: str = "http://localhost:8080"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
