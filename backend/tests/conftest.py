from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.identity_api import password_hasher
from app.main import app
from app.models import Base, Permission, Role, User
from app.rate_limit import limiter

ADMIN_PASSWORD = "sicheres-test-passwort-2026"
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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
