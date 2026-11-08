import pytest
from pydantic import ValidationError

from app.config import Settings


def test_database_password_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="SESSION_COOKIE_SECURE"):
        Settings(
            _env_file=None,
            postgres_password="test-only-not-for-production",
            app_env="production",
            session_cookie_secure=False,
            rate_limit_storage_uri="redis://localhost:6379/0",
        )


def test_production_requires_shared_rate_limit_storage() -> None:
    with pytest.raises(ValidationError, match="gemeinsamen Redis-Rate-Limit-Speicher"):
        Settings(
            _env_file=None,
            postgres_password="test-only-not-for-production",
            app_env="production",
            rate_limit_storage_uri="memory://",
        )


def test_production_requires_redis_host() -> None:
    with pytest.raises(ValidationError, match="gemeinsamen Redis-Rate-Limit-Speicher"):
        Settings(
            _env_file=None,
            postgres_password="test-only-not-for-production",
            app_env="production",
            rate_limit_storage_uri="redis:///",
        )


def test_production_rejects_wildcard_proxy_trust() -> None:
    with pytest.raises(ValidationError, match="nicht-wildcard Proxy-IP-Liste"):
        Settings(
            _env_file=None,
            postgres_password="test-only-not-for-production",
            app_env="production",
            rate_limit_storage_uri="redis://localhost:6379/0",
            forwarded_allow_ips="*",
        )


def test_production_accepts_redis_and_secure_cookies() -> None:
    settings = Settings(
        _env_file=None,
        postgres_password="test-only-not-for-production",
        app_env="production",
        session_cookie_secure=True,
        rate_limit_storage_uri="rediss://cache.example.test/0",
        forwarded_allow_ips="172.28.0.10",
    )

    assert settings.session_cookie_secure
