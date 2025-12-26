from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "tbslerp-api"
    version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60
    api_key_salt: str = "dev-api-key-salt"

    database_url: str = "postgresql+asyncpg://erp:erp@localhost:5432/erp"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Return a sync URL for Alembic migrations."""
        if "+asyncpg" in self.database_url:
            return self.database_url.replace("+asyncpg", "", 1)
        return self.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


