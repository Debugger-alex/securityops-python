from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base

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
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_customer_lifecycle_and_search(client: TestClient) -> None:
    created = client.post(
        "/api/v1/customers",
        json={
            "company_name": "Muster Sicherheitsdienst GmbH",
            "email": "kontakt@example.de",
            "phone": "+49 30 123456",
        },
    )
    assert created.status_code == 201
    customer = created.json()
    assert customer["customer_number"].startswith("K-")
    assert customer["status"] == "active"

    page = client.get("/api/v1/customers", params={"q": "Muster"})
    assert page.status_code == 200
    assert page.json()["total"] == 1
    assert page.json()["items"][0]["id"] == customer["id"]

    updated = client.patch(
        f"/api/v1/customers/{customer['id']}", json={"status": "inactive"}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "inactive"

    dashboard = client.get("/api/v1/dashboard")
    assert dashboard.json() == {
        "customers_total": 1,
        "customers_active": 0,
        "customers_leads": 0,
    }


def test_customer_validation_and_missing_record(client: TestClient) -> None:
    assert client.post("/api/v1/customers", json={"company_name": ""}).status_code == 422
    assert client.post("/api/v1/customers", json={"company_name": "   "}).status_code == 422
    assert (
        client.get("/api/v1/customers/00000000-0000-0000-0000-000000000000").status_code
        == 404
    )
