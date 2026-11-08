from datetime import date, timedelta
from uuid import UUID

from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.identity_api import password_hasher
from app.models import Role, User


def sign_in_as(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def create_test_user(username: str, role_code: str) -> UUID:
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == role_code))
        assert role is not None
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=f"Test {username}",
            password_hash=password_hasher.hash("personal-test-passwort-2026"),
            roles=[role],
        )
        db.add(user)
        db.commit()
        return user.id


def test_employee_management_qualification_expiry_and_retention(client: TestClient) -> None:
    admin_headers = {"X-CSRF-Token": sign_in_as(client, "admin", ADMIN_PASSWORD)}
    employee_user_id = create_test_user("mitarbeiterkonto", "employee")
    today = date.today()
    created = client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={
            "employee_number": "P-1001",
            "user_id": str(employee_user_id),
            "full_name": "Testperson Beispiel",
            "email": "PERSON@example.com",
            "job_title": "Sicherheitsmitarbeiter",
            "hired_on": str(today - timedelta(days=30)),
            "contract_type": "Vollzeit",
            "weekly_hours": 40,
        },
    )
    assert created.status_code == 201
    employee = created.json()
    assert employee["email"] == "person@example.com"
    assert employee["user_id"] == str(employee_user_id)
    assert "address" not in employee
    assert "internal_notes" not in employee
    assert (
        client.patch(
            f"/api/v1/employees/{employee['id']}",
            headers=admin_headers,
            json={"hired_on": None},
        ).status_code
        == 422
    )

    absence = client.post(
        f"/api/v1/employees/{employee['id']}/absences",
        headers=admin_headers,
        json={
            "absence_type": "vacation",
            "starts_on": str(today + timedelta(days=5)),
            "ends_on": str(today + timedelta(days=9)),
        },
    )
    assert absence.status_code == 201
    invalid_absence = client.post(
        f"/api/v1/employees/{employee['id']}/absences",
        headers=admin_headers,
        json={
            "absence_type": "vacation",
            "starts_on": str(today + timedelta(days=9)),
            "ends_on": str(today + timedelta(days=5)),
        },
    )
    assert invalid_absence.status_code == 422
    approved_absence = client.patch(
        f"/api/v1/employees/{employee['id']}/absences/{absence.json()['id']}",
        headers=admin_headers,
        json={"status": "approved"},
    )
    assert approved_absence.status_code == 200
    assert approved_absence.json()["status"] == "approved"

    duplicate = client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={
            "employee_number": "P-1001",
            "full_name": "Andere Person",
            "hired_on": str(today),
        },
    )
    assert duplicate.status_code == 409
    assert client.get("/api/v1/employees").json()["total"] == 1

    invalid_dates = client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={
            "employee_number": "P-1002",
            "full_name": "Ungültige Datumsangaben",
            "hired_on": str(today),
            "ended_on": str(today - timedelta(days=1)),
        },
    )
    assert invalid_dates.status_code == 422

    qualification = client.post(
        f"/api/v1/employees/{employee['id']}/qualifications",
        headers=admin_headers,
        json={
            "category": "Unterweisung",
            "name": "Arbeitsschutz",
            "issuer": "Interne Schulung",
            "valid_from": str(today - timedelta(days=20)),
            "expires_on": str(today + timedelta(days=10)),
        },
    )
    assert qualification.status_code == 201
    assert (
        client.patch(
            f"/api/v1/employees/{employee['id']}/qualifications/{qualification.json()['id']}",
            headers=admin_headers,
            json={"name": None},
        ).status_code
        == 422
    )
    past_due = client.post(
        f"/api/v1/employees/{employee['id']}/qualifications",
        headers=admin_headers,
        json={
            "category": "Zertifikat",
            "name": "Erste Hilfe",
            "expires_on": str(today - timedelta(days=2)),
        },
    )
    assert past_due.status_code == 201
    far_future = client.post(
        f"/api/v1/employees/{employee['id']}/qualifications",
        headers=admin_headers,
        json={
            "category": "Qualifikation",
            "name": "Brandschutz",
            "expires_on": str(today + timedelta(days=90)),
        },
    )
    assert far_future.status_code == 201

    invalid_qualification_dates = client.post(
        f"/api/v1/employees/{employee['id']}/qualifications",
        headers=admin_headers,
        json={
            "category": "Zertifikat",
            "name": "Ungültig",
            "valid_from": str(today),
            "expires_on": str(today - timedelta(days=1)),
        },
    )
    assert invalid_qualification_dates.status_code == 422

    expiring = client.get("/api/v1/employees/qualifications/expiring", params={"days": 30})
    assert expiring.status_code == 200
    assert {row["name"] for row in expiring.json()} == {"Arbeitsschutz", "Erste Hilfe"}
    overdue = next(row for row in expiring.json() if row["name"] == "Erste Hilfe")
    assert overdue["days_until_expiry"] == -2

    archived_qualification = client.post(
        f"/api/v1/employees/{employee['id']}/qualifications/{qualification.json()['id']}/archive",
        headers=admin_headers,
    )
    assert archived_qualification.status_code == 200
    assert len(client.get(f"/api/v1/employees/{employee['id']}/qualifications").json()) == 2
    assert (
        len(
            client.get(
                f"/api/v1/employees/{employee['id']}/qualifications",
                params={"include_archived": True},
            ).json()
        )
        == 3
    )

    archived_employee = client.post(
        f"/api/v1/employees/{employee['id']}/archive",
        headers=admin_headers,
    )
    assert archived_employee.status_code == 200
    assert archived_employee.json()["archived_at"] is not None
    assert client.get("/api/v1/employees").json()["total"] == 0
    assert client.get("/api/v1/employees", params={"include_archived": True}).json()["total"] == 1
    assert len(client.get(f"/api/v1/employees/{employee['id']}/qualifications").json()) == 2
    assert len(client.get(f"/api/v1/employees/{employee['id']}/absences").json()) == 1
    history = client.get(f"/api/v1/employees/{employee['id']}/history")
    assert history.status_code == 200
    assert {row["action"] for row in history.json()} >= {
        "created",
        "qualification_created",
        "qualification_archived",
        "absence_created",
        "absence_updated",
        "archived",
    }

    reactivated = client.post(
        f"/api/v1/employees/{employee['id']}/reactivate",
        headers=admin_headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["archived_at"] is None


def test_sensitive_employee_details_are_separately_authorized(client: TestClient) -> None:
    admin_headers = {"X-CSRF-Token": sign_in_as(client, "admin", ADMIN_PASSWORD)}
    employee = client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={
            "employee_number": "P-2001",
            "full_name": "Sensible Testperson",
            "hired_on": str(date.today()),
        },
    ).json()
    saved = client.patch(
        f"/api/v1/employees/{employee['id']}/sensitive",
        headers=admin_headers,
        json={
            "address": "Beispielstraße 1, 12345 Beispielstadt",
            "emergency_contact": "Testkontakt 0123 456789",
            "internal_notes": "Nur für berechtigte Personalverwaltung",
        },
    )
    assert saved.status_code == 200
    assert "internal_notes" not in client.get("/api/v1/employees").json()["items"][0]
    assert "internal_notes" not in client.get(f"/api/v1/employees/{employee['id']}").json()

    create_test_user("personalverwaltung", "hr")
    sign_in_as(client, "personalverwaltung", "personal-test-passwort-2026")
    assert (
        client.get(f"/api/v1/employees/{employee['id']}/sensitive").json()["emergency_contact"]
        == "Testkontakt 0123 456789"
    )
    history = client.get(f"/api/v1/employees/{employee['id']}/history").json()
    sensitive_event = next(row for row in history if row["action"] == "sensitive_updated")
    assert "emergency_contact" in sensitive_event["changed_fields"]
    assert "Testkontakt 0123 456789" not in str(sensitive_event)

    create_test_user("personal-leser", "management")
    manager_headers = {
        "X-CSRF-Token": sign_in_as(client, "personal-leser", "personal-test-passwort-2026")
    }
    assert client.get("/api/v1/employees").status_code == 200
    assert client.get(f"/api/v1/employees/{employee['id']}/sensitive").status_code == 403
    assert (
        client.patch(
            f"/api/v1/employees/{employee['id']}/sensitive",
            headers=manager_headers,
            json={"internal_notes": "Keine Berechtigung"},
        ).status_code
        == 403
    )

    create_test_user("normaler-mitarbeiter", "employee")
    sign_in_as(client, "normaler-mitarbeiter", "personal-test-passwort-2026")
    assert client.get("/api/v1/employees").status_code == 403
