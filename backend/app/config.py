from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SecurityOps"
    api_prefix: str = "/api/v1"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "securityops"
    postgres_user: str = "securityops"
    postgres_password: SecretStr
    cors_origins: str = "http://localhost:5173"
    session_cookie_secure: bool = True
    session_idle_minutes: int = 30
    session_absolute_hours: int = 12
    document_storage_path: Path = Path("./.private-document-storage")
    document_max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0, le=100 * 1024 * 1024)

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
