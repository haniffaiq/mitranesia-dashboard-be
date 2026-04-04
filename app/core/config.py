from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", enable_decoding=False)

    app_name: str = "Mitra Revamp Dashboard API"
    app_env: str = "development"
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=480, alias="JWT_EXPIRE_MINUTES")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5001",
            "http://localhost:5002",
            "http://localhost:5173",
        ],
        alias="CORS_ORIGINS",
    )
    create_tables_on_start: bool = Field(default=False, alias="CREATE_TABLES_ON_START")
    default_superadmin_username: str = Field(..., alias="DEFAULT_SUPERADMIN_USERNAME")
    default_superadmin_password: str = Field(..., alias="DEFAULT_SUPERADMIN_PASSWORD")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
