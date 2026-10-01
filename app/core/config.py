from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "MK Construction API"
    environment: str = "development"
    debug: bool = False

    database_url: str = Field(
        default="mysql+aiomysql://root:root@127.0.0.1:3306/Mk"
    )

    jwt_secret_key: str = Field(default="change-this-to-a-long-random-secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:5173"

    redis_url: str | None = None

    max_gst_percentage: float = 28

    @field_validator("jwt_secret_key")
    @classmethod
    def secret_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("JWT_SECRET_KEY must not be empty")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def allow_unrestricted_cors(self) -> bool:
        return not self.is_production and self.cors_origins.strip() == "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
