from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from conftest import ADMIN_PASSWORD, TestingSessionLocal, test_engine
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError

from app.identity_api import password_hasher
from app.models import (
    Employee,
    ObjectAssignment,
    OWKSEvent,
    OWKSRoute,
    Role,
    SecurityObject,
    User,
)


def sign_in(client: TestClient, username: str = "admin", password: str = ADMIN_PASSWORD) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def create_object(client: TestClient, headers: dict[str, str], code: str) -> str:
    customer = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": f"Testkunde {code} Wachschutz GmbH"},
    )
    assert customer.status_code == 201
    response = client.post(
        "/api/v1/objects",
        headers=headers,
        json={"customer_id": customer.json()["id"], "name": f"Objekt {code}", "code": code},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_assigned_employee(object_id: str, username: str = "wachkraft") -> None:
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "employee"))
        assert role is not None
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name="Test Wachkraft",
            password_hash=password_hasher.hash("wachkraft-test-passwort-2026"),
            roles=[role],
        )
        db.add(user)
        db.flush()
        employee = Employee(
            employee_number=f"TEST-{username}",
            user_id=user.id,
            full_name=user.full_name,
            employment_status="active",
            hired_on=date(2026, 1, 1),
        )
        db.add(employee)
        obj = db.get(SecurityObject, UUID(object_id))
        assert obj is not None
        db.add(ObjectAssignment(object_id=obj.id, user_id=user.id))
        db.commit()


def create_object_manager(object_id: str, username: str) -> None:
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "object_manager"))
        obj = db.get(SecurityObject, UUID(object_id))
        assert role is not None and obj is not None
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name="Test Objektleitung",
            password_hash=password_hasher.hash("objektleitung-test-passwort-2026"),
            roles=[role],
        )
        db.add(user)
        db.flush()
        db.add(ObjectAssignment(object_id=obj.id, user_id=user.id))
        db.commit()


def test_object_scoping_scan_replay_route_monitor_and_timestamp(client: TestClient) -> None:
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    object_id = create_object(client, admin_headers, "OWKS-001")
    other_object_id = create_object(client, admin_headers, "OWKS-002")
    create_assigned_employee(object_id)

    point_response = client.post(
        f"/api/v1/owks/objects/{object_id}/control-points",
        headers=admin_headers,
        json={"name": "Haupteingang", "identifier_type": "qr"},
    )
    assert point_response.status_code == 201
    point = point_response.json()
    credential = point["credential"]
    assert credential
    foreign_point = client.post(
        f"/api/v1/owks/objects/{other_object_id}/control-points",
        headers=admin_headers,
        json={"name": "Fremder Kontrollpunkt", "identifier_type": "nfc"},
    )
    assert foreign_point.status_code == 201
    listed_point = client.get(f"/api/v1/owks/objects/{object_id}/control-points")
    assert listed_point.status_code == 200
    assert "credential" not in listed_point.json()[0]

    route_response = client.post(
        f"/api/v1/owks/objects/{object_id}/routes",
        headers=admin_headers,
        json={
            "name": "Außenrunde",
            "interval_minutes": 1,
            "control_point_ids": [point["id"]],
        },
    )
    assert route_response.status_code == 201
    route_id = route_response.json()["id"]
    with TestingSessionLocal() as db:
        route = db.scalar(select(OWKSRoute))
        assert route is not None
        route.created_at = datetime.now(UTC) - timedelta(hours=2)
        db.commit()
    missed = client.post(f"/api/v1/owks/routes/{route_id}/monitor", headers=admin_headers)
    assert missed.status_code == 200
    assert len(missed.json()) == 1
    assert missed.json()[0]["event_type"] == "missed"
    assert (
        client.post(f"/api/v1/owks/routes/{route_id}/monitor", headers=admin_headers).json() == []
    )

    user_headers = {"X-CSRF-Token": sign_in(client, "wachkraft", "wachkraft-test-passwort-2026")}
    visible_objects = client.get("/api/v1/owks/objects")
    assert visible_objects.status_code == 200
    assert [item["id"] for item in visible_objects.json()] == [object_id]
    assert client.get(f"/api/v1/owks/objects/{other_object_id}/events").status_code == 404
    assert (
        client.post(
            f"/api/v1/owks/objects/{other_object_id}/challenges",
            headers=user_headers,
        ).status_code
        == 404
    )

    challenge = client.post(
        f"/api/v1/owks/objects/{object_id}/challenges",
        headers=user_headers,
    )
    assert challenge.status_code == 200
    foreign_scan = client.post(
        "/api/v1/owks/scans",
        headers=user_headers,
        json={
            "challenge_id": challenge.json()["id"],
            "credential": foreign_point.json()["credential"],
            "client_event_id": str(uuid4()),
        },
    )
    assert foreign_scan.status_code == 409
    scan_id = str(uuid4())
    scan = client.post(
        "/api/v1/owks/scans",
        headers=user_headers,
        json={
            "challenge_id": challenge.json()["id"],
            "credential": credential,
            "client_event_id": scan_id,
            "route_id": route_id,
        },
    )
    assert scan.status_code == 201
    assert scan.json()["event_type"] == "control"
    assert scan.json()["employee_id"]
    repeated_scan = client.post(
        "/api/v1/owks/scans",
        headers=user_headers,
        json={
            "challenge_id": challenge.json()["id"],
            "credential": credential,
            "client_event_id": scan_id,
            "route_id": route_id,
        },
    )
    assert repeated_scan.status_code == 201
    assert repeated_scan.json()["id"] == scan.json()["id"]
    conflicting_scan = client.post(
        "/api/v1/owks/scans",
        headers=user_headers,
        json={
            "challenge_id": challenge.json()["id"],
            "credential": foreign_point.json()["credential"],
            "client_event_id": scan_id,
            "route_id": route_id,
        },
    )
    assert conflicting_scan.status_code == 409
    replay = client.post(
        "/api/v1/owks/scans",
        headers=user_headers,
        json={
            "challenge_id": challenge.json()["id"],
            "credential": credential,
            "client_event_id": str(uuid4()),
            "route_id": route_id,
        },
    )
    assert replay.status_code == 409
    replay_events = client.get(f"/api/v1/owks/objects/{object_id}/events").json()
    assert any(event["event_type"] == "manipulation" for event in replay_events)


def test_offline_sync_conflicts_status_corrections_and_secure_attachments(
    client: TestClient,
) -> None:
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    object_id = create_object(client, admin_headers, "OWKS-003")
    create_assigned_employee(object_id, "syncwache")
    employee_headers = {
        "X-CSRF-Token": sign_in(client, "syncwache", "wachkraft-test-passwort-2026")
    }
    offline_id = str(uuid4())
    timestamp = "2026-11-08T19:00:00Z"
    sync = client.post(
        "/api/v1/owks/events/sync",
        headers=employee_headers,
        json=[
            {
                "object_id": object_id,
                "event_type": "handover",
                "title": "Übergabe Nachtschicht",
                "description": "Schlüssel übergeben.",
                "severity": "info",
                "occurred_at": timestamp,
                "client_event_id": offline_id,
            },
            {
                "object_id": object_id,
                "event_type": "control",
                "title": "Offline-Rundgang",
                "description": "Vor Ort notiert.",
                "severity": "info",
                "occurred_at": timestamp,
                "client_event_id": str(uuid4()),
            },
        ],
    )
    assert sync.status_code == 200
    assert [item["status"] for item in sync.json()] == ["synced", "conflict"]
    conflict_event = sync.json()[1]["event"]
    assert conflict_event["sync_status"] == "conflict"
    repeated = client.post(
        "/api/v1/owks/events/sync",
        headers=employee_headers,
        json=[
            {
                "object_id": object_id,
                "event_type": "handover",
                "title": "Übergabe Nachtschicht",
                "description": "Schlüssel übergeben.",
                "severity": "info",
                "occurred_at": timestamp,
                "client_event_id": offline_id,
            }
        ],
    )
    assert repeated.json()[0]["status"] == "duplicate"
    changed_replay = client.post(
        "/api/v1/owks/events/sync",
        headers=employee_headers,
        json=[
            {
                "object_id": object_id,
                "event_type": "handover",
                "title": "Manipulierter Wiederholungsversuch",
                "description": "",
                "severity": "info",
                "occurred_at": timestamp,
                "client_event_id": offline_id,
            }
        ],
    )
    assert changed_replay.json()[0]["status"] == "conflict"

    critical = client.post(
        "/api/v1/owks/events",
        headers=employee_headers,
        json={
            "object_id": object_id,
            "event_type": "deviation",
            "title": "Kritische Abweichung",
            "description": "Ursprünglicher Eintrag",
            "severity": "critical",
            "client_event_id": str(uuid4()),
        },
    )
    assert critical.status_code == 201
    critical_id = critical.json()["id"]
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    status_update = client.post(
        f"/api/v1/owks/events/{critical_id}/status",
        headers=admin_headers,
        json={"status": "in_progress", "note": "In Prüfung"},
    )
    assert status_update.status_code == 200
    status_update = client.post(
        f"/api/v1/owks/events/{critical_id}/status",
        headers=admin_headers,
        json={"status": "resolved", "note": "Geprüft"},
    )
    assert status_update.status_code == 200
    correction = client.post(
        f"/api/v1/owks/events/{critical_id}/corrections",
        headers=admin_headers,
        json={"reason": "Ergänzung nach Prüfung", "client_event_id": str(uuid4())},
    )
    assert correction.status_code == 201
    assert correction.json()["corrects_event_id"] == critical_id
    original = client.get(f"/api/v1/owks/objects/{object_id}/events").json()
    original_event = next(item for item in original if item["id"] == critical_id)
    assert original_event["description"] == "Ursprünglicher Eintrag"
    assert original_event["severity"] == "critical"
    assert original_event["status"] == "resolved"

    valid_pdf = b"%PDF-1.4\nTestdokument\n%%EOF"
    uploaded = client.post(
        f"/api/v1/owks/events/{critical_id}/attachments",
        headers=admin_headers,
        files={"document": ("bericht.pdf", valid_pdf, "application/pdf")},
    )
    assert uploaded.status_code == 201
    attachment_id = uploaded.json()["id"]
    downloaded = client.get(
        f"/api/v1/owks/events/{critical_id}/attachments/{attachment_id}",
        params={"download": "true"},
    )
    assert downloaded.status_code == 200
    assert downloaded.content == valid_pdf
    assert downloaded.headers["cache-control"] == "private, no-store"
    assert "sandbox" in downloaded.headers["content-security-policy"]
    invalid = client.post(
        f"/api/v1/owks/events/{critical_id}/attachments",
        headers=admin_headers,
        files={"document": ("fake.pdf", b"not a PDF", "application/pdf")},
    )
    assert invalid.status_code == 415


def test_owks_permission_and_foreign_object_attachment_are_denied(client: TestClient) -> None:
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    object_id = create_object(client, admin_headers, "OWKS-004")
    other_object_id = create_object(client, admin_headers, "OWKS-005")
    create_assigned_employee(object_id, "isolatedwache")
    create_assigned_employee(other_object_id, "fremdewache")
    event = client.post(
        "/api/v1/owks/events",
        headers={"X-CSRF-Token": sign_in(client, "isolatedwache", "wachkraft-test-passwort-2026")},
        json={
            "object_id": object_id,
            "event_type": "entry",
            "title": "Wachbuchzugriff",
            "description": "",
            "severity": "info",
            "client_event_id": str(uuid4()),
        },
    )
    assert event.status_code == 201
    assert client.get(f"/api/v1/owks/objects/{object_id}/events").status_code == 200
    assert client.get("/api/v1/owks/objects").status_code == 200
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    uploaded = client.post(
        f"/api/v1/owks/events/{event.json()['id']}/attachments",
        headers=admin_headers,
        files={"document": ("bericht.pdf", b"%PDF-1.4\nprivat\n", "application/pdf")},
    )
    assert uploaded.status_code == 201
    foreign_headers = {
        "X-CSRF-Token": sign_in(client, "fremdewache", "wachkraft-test-passwort-2026")
    }
    foreign_download = client.get(
        f"/api/v1/owks/events/{event.json()['id']}/attachments/{uploaded.json()['id']}"
    )
    assert foreign_download.status_code == 404
    assert (
        client.post(
            f"/api/v1/owks/objects/{object_id}/challenges",
            headers=foreign_headers,
        ).status_code
        == 404
    )

    create_object_manager(object_id, "leitung-ohne-owks")
    sign_in(client, "leitung-ohne-owks", "objektleitung-test-passwort-2026")
    assert client.get(f"/api/v1/owks/objects/{object_id}/events").status_code == 403


@pytest.mark.skipif(
    test_engine.dialect.name != "postgresql",
    reason="Append-only-Trigger wird in PostgreSQL geprüft",
)
def test_owks_events_are_database_append_only(client: TestClient) -> None:
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    object_id = create_object(client, admin_headers, "OWKS-006")
    create_assigned_employee(object_id, "triggerwache")
    employee_headers = {
        "X-CSRF-Token": sign_in(client, "triggerwache", "wachkraft-test-passwort-2026")
    }
    created = client.post(
        "/api/v1/owks/events",
        headers=employee_headers,
        json={
            "object_id": object_id,
            "event_type": "entry",
            "title": "Unveränderlicher Eintrag",
            "description": "Original",
            "severity": "critical",
            "client_event_id": str(uuid4()),
        },
    )
    assert created.status_code == 201
    with TestingSessionLocal() as db:
        with pytest.raises(DBAPIError):
            db.execute(
                update(OWKSEvent)
                .where(OWKSEvent.id == created.json()["id"])
                .values(description="unzulässig")
            )
        db.rollback()
