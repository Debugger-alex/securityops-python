from collections.abc import Generator
import os

os.environ.setdefault("POSTGRES_PASSWORD", "test-only-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.identity_api import password_hasher
from app.main import app
from app.models import Base, Permission, Role, User
from app.rate_limit import limiter

ADMIN_PASSWORD = "sicheres-test-passwort-2026"
test_database_url = os.environ.get("SECURITYOPS_TEST_DATABASE_URL", "sqlite://")
engine_options = {}
if test_database_url == "sqlite://":
    engine_options = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
else:
    parsed_test_url = make_url(test_database_url)
    if (
        parsed_test_url.drivername != "postgresql+psycopg"
        or parsed_test_url.host not in {"localhost", "127.0.0.1"}
        or parsed_test_url.database != "securityops_test"
    ):
        raise RuntimeError(
            "PostgreSQL-Tests sind nur für localhost/securityops_test zulässig."
        )
test_engine = create_engine(test_database_url, **engine_options)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    limiter.reset()
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as db:
        permission_codes = (
            "customers.read",
            "customers.create",
            "customers.update",
            "dashboard.read",
            "users.read",
            "users.manage",
            "roles.read",
            "audit.read",
            "owks.read",
        )
        permissions = {code: Permission(code=code, description=code) for code in permission_codes}
        administrator = Role(
            code="administrator",
            name="Administrator",
            description="Testrolle",
            permissions=list(permissions.values()),
        )
        management = Role(
            code="management",
            name="Geschäftsführung",
            description="Testrolle ohne Administratorrechte",
            permissions=[
                permissions["users.read"],
                permissions["users.manage"],
                permissions["customers.read"],
            ],
        )
        employee = Role(
            code="employee",
            name="Mitarbeiter",
            description="Operative Testrolle",
            permissions=[permissions["owks.read"]],
        )
        db.add_all([administrator, management, employee])
        db.add(
            User(
                username="admin",
                email="admin@example.com",
                full_name="Test Administration",
                password_hash=password_hasher.hash(ADMIN_PASSWORD),
                roles=[administrator],
            )
        )
        db.add(
            User(
                username="geschaeftsfuehrung",
                email="management@example.com",
                full_name="Test Geschäftsführung",
                password_hash=password_hasher.hash("management-test-passwort-2026"),
                roles=[management],
            )
        )
        db.commit()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    limiter.reset()
