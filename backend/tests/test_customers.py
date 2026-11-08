from conftest import ADMIN_PASSWORD
from fastapi.testclient import TestClient


def sign_in(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def test_customer_lifecycle_and_search(client: TestClient) -> None:
    csrf_token = sign_in(client)
    headers = {"X-CSRF-Token": csrf_token}
    created = client.post(
        "/api/v1/customers",
        json={
            "company_name": "Muster Sicherheitsdienst GmbH",
            "email": "kontakt@example.de",
            "phone": "+49 30 123456",
        },
        headers=headers,
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
        f"/api/v1/customers/{customer['id']}",
        json={"status": "inactive"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "inactive"

    dashboard = client.get("/api/v1/dashboard")
    assert dashboard.json() == {
        "customers_total": 1,
        "customers_active": 0,
        "customers_leads": 0,
    }
    audit_actions = {row["action"] for row in client.get("/api/v1/audit-logs").json()}
    assert {"customers.created", "customers.updated"} <= audit_actions


def test_customer_validation_and_missing_record(client: TestClient) -> None:
    csrf_token = sign_in(client)
    headers = {"X-CSRF-Token": csrf_token}
    assert (
        client.post("/api/v1/customers", json={"company_name": ""}, headers=headers).status_code
        == 422
    )
    assert (
        client.post("/api/v1/customers", json={"company_name": "   "}, headers=headers).status_code
        == 422
    )
    assert client.get("/api/v1/customers/00000000-0000-0000-0000-000000000000").status_code == 404
