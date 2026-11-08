import base64
from types import SimpleNamespace
from uuid import UUID, uuid4

from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient

from app.models import ObjectSensitiveData


def sign_in(client: TestClient, username: str = "admin", password: str = ADMIN_PASSWORD) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def create_customer(client: TestClient, headers: dict[str, str], name: str = "Beispiel GmbH"):
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": name},
    )
    assert response.status_code == 201
    return response.json()


def create_object(client: TestClient, headers: dict[str, str], customer_id: str, **overrides):
    payload = {
        "customer_id": customer_id,
        "name": "Logistikzentrum Nord",
        "street": "Hafenstraße",
        "house_number": "12",
        "postal_code": "20457",
        "city": "Hamburg",
        "operating_hours": {
            "monday": [{"start": "06:00", "end": "22:00"}],
        },
        "required_staffing": 2,
        "qualification_requirements": ["Sachkunde § 34a"],
        **overrides,
    }
    return client.post("/api/v1/objects", headers=headers, json=payload)


def test_object_crud_contacts_search_and_history(client: TestClient) -> None:
    headers = {"X-CSRF-Token": sign_in(client)}
    customer = create_customer(client, headers)
    created = create_object(client, headers, customer["id"])
    assert created.status_code == 201
    site = created.json()
    object_id = site["id"]
    assert site["object_number"].startswith("O-")
    assert site["customer_name"] == customer["company_name"]
    assert site["operating_hours"]["monday"] == [{"start": "06:00:00", "end": "22:00:00"}]
    assert "alarm_information" not in site

    contact = client.post(
        f"/api/v1/objects/{object_id}/contacts",
        headers=headers,
        json={
            "first_name": "Mara",
            "last_name": "Beispiel",
            "responsibility": "Standortleitung",
            "email": "mara@example.de",
            "is_primary": True,
        },
    )
    assert contact.status_code == 201
    second_contact = client.post(
        f"/api/v1/objects/{object_id}/contacts",
        headers=headers,
        json={"first_name": "Timo", "last_name": "Muster"},
    )
    assert second_contact.status_code == 201
    promoted = client.patch(
        f"/api/v1/objects/{object_id}/contacts/{second_contact.json()['id']}",
        headers=headers,
        json={"is_primary": True},
    )
    assert promoted.status_code == 200
    contacts = client.get(f"/api/v1/objects/{object_id}/contacts").json()
    assert sum(contact_item["is_primary"] for contact_item in contacts) == 1

    updated = client.patch(
        f"/api/v1/objects/{object_id}",
        headers=headers,
        json={
            "service_instructions": "Zutrittskontrolle am Haupteingang.",
            "required_staffing": 3,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["required_staffing"] == 3
    assert client.get("/api/v1/objects", params={"q": "Hafenstraße"}).json()["total"] == 1
    assert client.get("/api/v1/objects", params={"q": "Hamburg"}).json()["total"] == 1
    assert (
        client.get("/api/v1/objects", params={"customer_id": customer["id"]}).json()["total"] == 1
    )

    history = client.get(f"/api/v1/objects/{object_id}/history")
    assert history.status_code == 200
    assert {row["action"] for row in history.json()} >= {
        "created",
        "contact_created",
        "contact_updated",
        "updated",
    }
    assert (
        client.patch(
            f"/api/v1/objects/{object_id}",
            headers=headers,
            json={"name": "   "},
        ).status_code
        == 422
    )
    assert (
        create_object(
            client,
            headers,
            customer["id"],
            operating_hours={
                "monday": [
                    {"start": "08:00", "end": "12:00"},
                    {"start": "11:00", "end": "15:00"},
                ]
            },
        ).status_code
        == 422
    )


def test_object_customer_integrity_archiving_and_assignment_scope(client: TestClient) -> None:
    headers = {"X-CSRF-Token": sign_in(client)}
    customer = create_customer(client, headers)
    second_customer = create_customer(client, headers, "Zweitkunde GmbH")
    first = create_object(client, headers, customer["id"]).json()
    second = create_object(client, headers, second_customer["id"], name="Zweiter Standort").json()

    reassigned = client.patch(
        f"/api/v1/objects/{first['id']}",
        headers=headers,
        json={"customer_id": second_customer["id"]},
    )
    assert reassigned.status_code == 200
    assert reassigned.json()["customer_id"] == second_customer["id"]

    missing_customer = create_object(client, headers, str(uuid4()))
    assert missing_customer.status_code == 422
    archived_customer = client.post(
        f"/api/v1/customers/{customer['id']}/archive",
        headers=headers,
    )
    assert archived_customer.status_code == 200
    assert create_object(client, headers, customer["id"]).status_code == 409

    manager = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "objektleitung",
            "email": "objektleitung@example.de",
            "full_name": "Test Objektleitung",
            "password": "test-passwort-objektleitung-2026",
            "role_codes": ["object_manager"],
        },
    )
    assert manager.status_code == 201
    candidates = client.get("/api/v1/objects/assignment-candidates")
    assert candidates.status_code == 200
    assert manager.json()["id"] in {candidate["id"] for candidate in candidates.json()}
    assignment = client.post(
        f"/api/v1/objects/{first['id']}/assignments",
        headers=headers,
        json={"user_id": manager.json()["id"]},
    )
    assert assignment.status_code == 201
    manager_update = client.patch(
        f"/api/v1/objects/{first['id']}",
        headers=headers,
        json={"object_manager_user_id": manager.json()["id"]},
    )
    assert manager_update.status_code == 200
    assert manager_update.json()["object_manager_user_id"] == manager.json()["id"]
    assert (
        client.delete(
            f"/api/v1/objects/{first['id']}/assignments/{manager.json()['id']}",
            headers=headers,
        ).status_code
        == 409
    )
    assert client.get(f"/api/v1/objects/{second['id']}/assignments").status_code == 200

    manager_csrf = sign_in(client, "objektleitung", "test-passwort-objektleitung-2026")
    scoped_page = client.get("/api/v1/objects")
    assert scoped_page.status_code == 200
    assert [item["id"] for item in scoped_page.json()["items"]] == [first["id"]]
    assert client.get(f"/api/v1/objects/{second['id']}").status_code == 404
    assert (
        client.patch(
            f"/api/v1/objects/{second['id']}",
            headers={"X-CSRF-Token": manager_csrf},
            json={"name": "Nicht erlaubt"},
        ).status_code
        == 404
    )
    assert client.get(f"/api/v1/objects/{first['id']}/sensitive-data").status_code == 403

    admin_csrf = sign_in(client)
    archived_object = client.post(
        f"/api/v1/objects/{first['id']}/archive",
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert archived_object.status_code == 200
    assert client.get("/api/v1/objects").json()["total"] == 1
    assert client.get("/api/v1/objects", params={"include_archived": True}).json()["total"] == 2
    assert (
        client.patch(
            f"/api/v1/objects/{first['id']}",
            headers={"X-CSRF-Token": admin_csrf},
            json={"name": "Archivierte Änderung"},
        ).status_code
        == 409
    )


def test_sensitive_object_information_requires_key_and_is_encrypted(
    client: TestClient,
    monkeypatch,
) -> None:
    headers = {"X-CSRF-Token": sign_in(client)}
    customer = create_customer(client, headers)
    site = create_object(client, headers, customer["id"]).json()
    endpoint = f"/api/v1/objects/{site['id']}/sensitive-data"
    secret_payload = {
        "alarm_information": "Alarmzentrale im abgeschlossenen Raum.",
        "emergency_information": "Notfallkontakt über Leitstelle.",
        "key_management": "Schlüsseltresor im gesicherten Büro.",
        "access_authorizations": "Nur eingewiesenes Personal.",
    }

    assert client.put(endpoint, headers=headers, json=secret_payload).status_code == 503
    key = base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef").decode("ascii")
    assert len(base64.urlsafe_b64decode(key)) == 32
    monkeypatch.setattr(
        "app.object_security.get_settings",
        lambda: SimpleNamespace(
            object_data_encryption_key=SimpleNamespace(get_secret_value=lambda: key)
        ),
    )
    stored = client.put(endpoint, headers=headers, json=secret_payload)
    assert stored.status_code == 200
    assert stored.json()["alarm_information"] == secret_payload["alarm_information"]
    with TestingSessionLocal() as db:
        record = db.get(ObjectSensitiveData, UUID(site["id"]))
        assert record is not None
        assert secret_payload["alarm_information"] not in record.ciphertext
    assert client.get(endpoint).json()["key_management"] == secret_payload["key_management"]
    assert client.get(f"/api/v1/objects/{site['id']}").json().get("key_management") is None
