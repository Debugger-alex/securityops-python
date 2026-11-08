from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SecurityOps"
    api_prefix: str = "/api/v1"
    app_env: Literal["development", "production"] = "development"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "securityops"
    postgres_user: str = "securityops"
    postgres_password: SecretStr
    cors_origins: str = "http://localhost:5173"
    session_cookie_secure: bool = True
    rate_limit_storage_uri: str = "memory://"
    forwarded_allow_ips: str = "127.0.0.1"
    session_idle_minutes: int = 30
    session_absolute_hours: int = 12
    document_storage_path: Path = Path("./.private-document-storage")
    document_max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0, le=100 * 1024 * 1024)

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            if not self.session_cookie_secure:
                raise ValueError("SESSION_COOKIE_SECURE muss in Produktion aktiviert sein.")
            rate_limit_url = urlsplit(self.rate_limit_storage_uri)
            if rate_limit_url.scheme not in {"redis", "rediss"} or not rate_limit_url.hostname:
                raise ValueError(
                    "Produktion erfordert einen gemeinsamen Redis-Rate-Limit-Speicher."
                )
            forwarded_ips = {
                address.strip()
                for address in self.forwarded_allow_ips.split(",")
                if address.strip()
            }
            if not forwarded_ips or "*" in forwarded_ips:
                raise ValueError(
                    "Produktion erfordert eine explizite, nicht-wildcard Proxy-IP-Liste."
                )
        return self

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
