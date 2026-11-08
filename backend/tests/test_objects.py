from uuid import uuid4

from conftest import ADMIN_PASSWORD
from fastapi.testclient import TestClient


def sign_in(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def test_object_lifecycle_and_history(client: TestClient) -> None:
    headers = {"X-CSRF-Token": sign_in(client)}
    customer = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Objektkunde Sicherheitsdienst GmbH"},
    )
    assert customer.status_code == 201
    customer_id = customer.json()["id"]

    created = client.post(
        "/api/v1/objects",
        headers=headers,
        json={
            "customer_id": customer_id,
            "name": "Turm West",
            "code": "OBJ-001",
            "object_type": "Wachschutz",
            "description": "Zentrales Objekt",
            "address": {
                "street": "Hafenstraße",
                "house_number": "12",
                "postal_code": "20457",
                "city": "Hamburg",
            },
            "contact": {
                "first_name": "Petra",
                "last_name": "Leiter",
                "role": "Objektverantwortliche",
                "email": "petra@example.de",
                "phone": "+49 40 123",
                "is_primary": True,
            },
        },
    )
    assert created.status_code == 201
    obj = created.json()
    assert obj["code"] == "OBJ-001"
    assert obj["name"] == "Turm West"
    assert obj["address"]["city"] == "Hamburg"
    assert obj["contacts"][0]["is_primary"] is True

    page = client.get("/api/v1/objects", params={"q": "Turm"})
    assert page.status_code == 200
    assert page.json()["total"] == 1

    updated = client.patch(
        f"/api/v1/objects/{obj['id']}",
        headers=headers,
        json={
            "description": "Aktualisierte Beschreibung",
            "address": {
                "street": "Bergstraße",
                "house_number": "8",
                "postal_code": "21073",
                "city": "Hamburg",
            },
        },
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Aktualisierte Beschreibung"
    assert updated.json()["address"]["street"] == "Bergstraße"

    archived = client.post(f"/api/v1/objects/{obj['id']}/archive", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None
    assert client.get("/api/v1/objects").json()["total"] == 0

    history = client.get(f"/api/v1/objects/{obj['id']}/history")
    assert history.status_code == 200
    assert {row["action"] for row in history.json()} >= {"created", "updated", "archived"}


def test_object_validation_and_customer_requirement(client: TestClient) -> None:
    headers = {"X-CSRF-Token": sign_in(client)}
    invalid = client.post(
        "/api/v1/objects",
        headers=headers,
        json={
            "customer_id": str(uuid4()),
            "name": "",
            "code": "OBJ-002",
        },
    )
    assert invalid.status_code == 422

    customer = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Kunde für Objektprüfung GmbH"},
    ).json()
    created = client.post(
        "/api/v1/objects",
        headers=headers,
        json={"customer_id": customer["id"], "name": "Prüfobjekt", "code": "OBJ-003"},
    )
    assert created.status_code == 201
    assert (
        client.post(
            f"/api/v1/objects/{created.json()['id']}/reactivate",
            headers=headers,
        ).status_code
        == 409
    )
