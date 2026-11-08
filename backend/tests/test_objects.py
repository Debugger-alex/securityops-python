from uuid import UUID, uuid4

from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.identity_api import password_hasher
from app.models import Role, User


def sign_in(client: TestClient) -> str:
    return sign_in_as(client, "admin", ADMIN_PASSWORD)


def sign_in_as(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def create_test_user(username: str, role_code: str) -> None:
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == role_code))
        assert role is not None
        db.add(
            User(
                username=username,
                email=f"{username}@example.com",
                full_name=f"Test {username}",
                password_hash=password_hasher.hash("objekt-test-passwort-2026"),
                roles=[role],
            )
        )
        db.commit()


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
            "contacts": [
                {
                    "first_name": "Petra",
                    "last_name": "Leiter",
                    "role": "Objektverantwortliche",
                    "email": "petra@example.de",
                    "phone": "+49 40 123",
                    "is_primary": True,
                },
                {
                    "first_name": "Timo",
                    "last_name": "Wache",
                    "role": "Stellvertretung",
                    "email": "timo@example.de",
                    "is_primary": False,
                },
            ],
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
    assert len(updated.json()["contacts"]) == 2

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


def test_object_access_is_limited_to_assignments(client: TestClient) -> None:
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    customer = client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"company_name": "Kunde für Zugriffstest GmbH"},
    ).json()
    created = client.post(
        "/api/v1/objects",
        headers=admin_headers,
        json={"customer_id": customer["id"], "name": "Zugewiesenes Objekt", "code": "OBJ-ACL-1"},
    )
    assert created.status_code == 201
    object_id = created.json()["id"]
    create_test_user("objektleitung", "object_manager")
    create_test_user("objektmitarbeiter", "employee")

    manager_headers = {
        "X-CSRF-Token": sign_in_as(client, "objektleitung", "objekt-test-passwort-2026")
    }
    assert client.get("/api/v1/objects").json()["total"] == 0
    assert client.get(f"/api/v1/objects/{object_id}").status_code == 404
    assert client.get(f"/api/v1/objects/{object_id}/history").status_code == 404
    assert client.get("/api/v1/objects/assignment-candidates").status_code == 403
    assert client.get(f"/api/v1/objects/{object_id}/assignments").status_code == 403
    assert (
        client.patch(
            f"/api/v1/objects/{object_id}",
            headers=manager_headers,
            json={"name": "Unberechtigte Änderung"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/objects/{object_id}/archive",
            headers=manager_headers,
        ).status_code
        == 404
    )

    admin_headers = {"X-CSRF-Token": sign_in_as(client, "admin", ADMIN_PASSWORD)}
    assigned = client.put(
        f"/api/v1/objects/{object_id}/assignments",
        headers=admin_headers,
        json={
            "user_ids": [
                str(get_user_id("objektleitung")),
                str(get_user_id("objektmitarbeiter")),
            ]
        },
    )
    assert assigned.status_code == 200
    assert len(assigned.json()) == 2

    manager_headers = {
        "X-CSRF-Token": sign_in_as(client, "objektleitung", "objekt-test-passwort-2026")
    }
    page = client.get("/api/v1/objects")
    assert page.status_code == 200
    assert [item["id"] for item in page.json()["items"]] == [object_id]
    assert client.get(f"/api/v1/objects/{object_id}").status_code == 200
    updated = client.patch(
        f"/api/v1/objects/{object_id}",
        headers=manager_headers,
        json={"name": "Zugewiesenes Objekt geändert"},
    )
    assert updated.status_code == 200

    employee_headers = {
        "X-CSRF-Token": sign_in_as(client, "objektmitarbeiter", "objekt-test-passwort-2026")
    }
    assert client.get("/api/v1/objects").json()["total"] == 1
    assert client.get(f"/api/v1/objects/{object_id}").status_code == 200
    assert (
        client.patch(
            f"/api/v1/objects/{object_id}",
            headers=employee_headers,
            json={"name": "Unberechtigte Mitarbeiteränderung"},
        ).status_code
        == 403
    )


def get_user_id(username: str) -> UUID:
    with TestingSessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        assert user is not None
        return user.id
