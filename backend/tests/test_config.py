import pytest
from pydantic import ValidationError

from app.config import Settings


def test_database_password_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
