import os
from collections.abc import Generator

os.environ.setdefault("POSTGRES_PASSWORD", "test-only-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.identity_api import password_hasher
from app.main import app
from app.models import (
    AuditLog,
    Base,
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerHistory,
    Permission,
    Role,
    User,
    UserSession,
    user_roles,
)
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
        raise RuntimeError("PostgreSQL-Tests sind nur für localhost/securityops_test zulässig.")
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
        db.execute(delete(UserSession))
        db.execute(delete(AuditLog))
        db.execute(delete(CustomerHistory))
        db.execute(delete(CustomerContact))
        db.execute(delete(CustomerAddress))
        db.execute(delete(Customer))
        db.execute(delete(user_roles))
        db.execute(delete(User))
        db.commit()

        permission_codes = (
            "customers.read",
            "customers.create",
            "customers.update",
            "customers.archive",
            "objects.read",
            "objects.manage",
            "dashboard.read",
            "users.read",
            "users.manage",
            "roles.read",
            "audit.read",
            "owks.read",
        )
        permissions = {}
        for code in permission_codes:
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                permission = Permission(code=code, description=code)
                db.add(permission)
            permissions[code] = permission

        def get_or_create_role(
            code: str,
            name: str,
            description: str,
            permission_codes: tuple[str, ...],
        ) -> Role:
            role = db.scalar(select(Role).where(Role.code == code))
            if role is None:
                role = Role(code=code, name=name, description=description)
                db.add(role)
            existing_codes = {permission.code for permission in role.permissions}
            role.permissions.extend(
                permissions[permission_code]
                for permission_code in permission_codes
                if permission_code not in existing_codes
            )
            return role

        administrator = get_or_create_role(
            "administrator",
            "Administrator",
            "Testrolle",
            permission_codes,
        )
        management = get_or_create_role(
            "management",
            "Geschäftsführung",
            "Testrolle ohne Administratorrechte",
            ("users.read", "users.manage", "customers.read", "objects.read", "objects.manage"),
        )
        get_or_create_role(
            "employee",
            "Mitarbeiter",
            "Operative Testrolle",
            ("owks.read",),
        )
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
    limiter.reset()
