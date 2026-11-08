from conftest import ADMIN_PASSWORD
from fastapi.testclient import TestClient


def sign_in(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def test_customer_details_contacts_and_history(client: TestClient) -> None:
    csrf_token = sign_in(client)
    headers = {"X-CSRF-Token": csrf_token}
    created = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "company_name": "Nordlicht Sicherheitsdienst GmbH",
            "legal_form": "GmbH",
            "vat_number": "DE123456789",
            "tax_number": "12/345/67890",
            "internal_notes": "Abrechnung monatlich prüfen.",
            "business_address": {
                "street": "Hafenstraße",
                "house_number": "12a",
                "postal_code": "20457",
                "city": "Hamburg",
                "country_code": "DE",
            },
            "billing_address": {
                "street": "Rechnungsweg",
                "house_number": "4",
                "postal_code": "20095",
                "city": "Hamburg",
            },
        },
    )
    assert created.status_code == 201
    customer = created.json()
    customer_id = customer["id"]
    assert customer["customer_number"].startswith("K-")
    assert customer["legal_form"] == "GmbH"
    assert customer["business_address"]["city"] == "Hamburg"
    assert customer["billing_address"]["street"] == "Rechnungsweg"

    primary = client.post(
        f"/api/v1/customers/{customer_id}/contacts",
        headers=headers,
        json={
            "first_name": "Anna",
            "last_name": "Beispiel",
            "responsibility": "Einsatzplanung",
            "email": "anna@example.de",
            "phone": "+49 40 123",
            "is_primary": True,
        },
    )
    assert primary.status_code == 201
    secondary = client.post(
        f"/api/v1/customers/{customer_id}/contacts",
        headers=headers,
        json={"first_name": "Max", "last_name": "Muster"},
    )
    assert secondary.status_code == 201

    updated = client.patch(
        f"/api/v1/customers/{customer_id}",
        headers=headers,
        json={
            "internal_notes": "Aktualisierte Notiz",
            "business_address": {
                "street": "Hafenstraße",
                "house_number": "14",
                "postal_code": "20457",
                "city": "Hamburg",
            },
        },
    )
    assert updated.status_code == 200
    assert updated.json()["business_address"]["house_number"] == "14"

    promoted = client.patch(
        f"/api/v1/customers/{customer_id}/contacts/{secondary.json()['id']}",
        headers=headers,
        json={"is_primary": True, "email": "max@example.de"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["is_primary"] is True
    detail = client.get(f"/api/v1/customers/{customer_id}")
    assert detail.status_code == 200
    assert [contact["is_primary"] for contact in detail.json()["contacts"]].count(True) == 1

    page = client.get("/api/v1/customers", params={"q": "max@example.de"})
    assert page.status_code == 200
    assert page.json()["total"] == 1
    page = client.get("/api/v1/customers", params={"q": "20457", "sort_by": "customer_number"})
    assert page.json()["total"] == 1

    history = client.get(f"/api/v1/customers/{customer_id}/history")
    assert history.status_code == 200
    assert {row["action"] for row in history.json()} >= {
        "created",
        "contact_created",
        "updated",
        "contact_updated",
    }
    assert all("Aktualisierte Notiz" not in str(row["changed_fields"]) for row in history.json())


def test_customer_archive_reactivation_and_contact_removal(client: TestClient) -> None:
    headers = {"X-CSRF-Token": sign_in(client)}
    customer = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Archiv GmbH"},
    ).json()
    contact = client.post(
        f"/api/v1/customers/{customer['id']}/contacts",
        headers=headers,
        json={"first_name": "Nina", "last_name": "Kontakt"},
    ).json()

    archived = client.post(f"/api/v1/customers/{customer['id']}/archive", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None
    assert client.get("/api/v1/customers").json()["total"] == 0
    assert client.get("/api/v1/customers", params={"include_archived": True}).json()["total"] == 1
    assert (
        client.patch(
            f"/api/v1/customers/{customer['id']}",
            headers=headers,
            json={"company_name": "Soll nicht gespeichert werden"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/customers/{customer['id']}/archive",
            headers=headers,
        ).status_code
        == 409
    )

    reactivated = client.post(
        f"/api/v1/customers/{customer['id']}/reactivate",
        headers=headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["archived_at"] is None
    assert (
        client.delete(
            f"/api/v1/customers/{customer['id']}/contacts/{contact['id']}",
            headers=headers,
        ).status_code
        == 204
    )
    assert client.get(f"/api/v1/customers/{customer['id']}").json()["contacts"] == []

    history = client.get(f"/api/v1/customers/{customer['id']}/history").json()
    assert {row["action"] for row in history} >= {
        "created",
        "archived",
        "reactivated",
        "contact_deleted",
    }
