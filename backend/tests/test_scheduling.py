from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, time, timedelta
from threading import Barrier
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from conftest import ADMIN_PASSWORD, TestingSessionLocal, test_engine
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.identity_api import password_hasher
from app.models import (
    EmployeeQualification,
    Role,
    ScheduleShift,
    User,
)


def sign_in(client: TestClient, username: str = "admin", password: str = ADMIN_PASSWORD) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return client.cookies.get("securityops_csrf", "")


def create_employee_user(username: str) -> UUID:
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "employee"))
        assert role is not None
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=f"Test {username}",
            password_hash=password_hasher.hash("dienstplan-test-passwort-2026"),
            roles=[role],
        )
        db.add(user)
        db.commit()
        return user.id


def setup_schedule(client: TestClient) -> tuple[dict, dict, str]:
    headers = {"X-CSRF-Token": sign_in(client)}
    user_id = create_employee_user("dienstplan-person")
    employee_response = client.post(
        "/api/v1/employees",
        headers=headers,
        json={
            "employee_number": "P-SCH-001",
            "user_id": str(user_id),
            "full_name": "Testperson Dienstplan",
            "hired_on": str(date.today() - timedelta(days=100)),
        },
    )
    assert employee_response.status_code == 201, employee_response.text
    employee = employee_response.json()

    customer = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Testkunde Dienstplanung"},
    )
    assert customer.status_code == 201, customer.text
    obj_response = client.post(
        "/api/v1/objects",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "name": "Testobjekt Dienstplanung",
            "code": "OBJ-SCH-001",
        },
    )
    assert obj_response.status_code == 201, obj_response.text
    obj = obj_response.json()
    assignment = client.put(
        f"/api/v1/objects/{obj['id']}/assignments",
        headers=headers,
        json={"user_ids": [str(user_id)]},
    )
    assert assignment.status_code == 200, assignment.text
    return employee, obj, headers["X-CSRF-Token"]


def shift_payload(employee: dict, obj: dict, starts_at: datetime, ends_at: datetime) -> dict:
    return {
        "employee_id": employee["id"],
        "object_id": obj["id"],
        "starts_at_local": starts_at.isoformat(timespec="minutes"),
        "ends_at_local": ends_at.isoformat(timespec="minutes"),
        "break_minutes": 30,
    }


def test_shift_creation_conflicts_publication_and_history(client: TestClient) -> None:
    employee, obj, csrf = setup_schedule(client)
    headers = {"X-CSRF-Token": csrf}
    starts_at = datetime.combine(date.today() + timedelta(days=40), time(9))
    payload = shift_payload(employee, obj, starts_at, starts_at + timedelta(hours=8))

    created = client.post("/api/v1/scheduling/shifts", headers=headers, json=payload)
    assert created.status_code == 201, created.text
    shift = created.json()
    assert shift["status"] == "draft"
    assert shift["time_zone"] == "Europe/Berlin"
    assert (
        datetime.fromisoformat(shift["starts_at"])
        .astimezone(ZoneInfo("Europe/Berlin"))
        .replace(tzinfo=None)
        == starts_at
    )
    updated = client.patch(
        f"/api/v1/scheduling/shifts/{shift['id']}",
        headers=headers,
        json={"break_minutes": 45},
    )
    assert updated.status_code == 200
    assert updated.json()["break_minutes"] == 45

    overlap = client.post(
        "/api/v1/scheduling/shifts",
        headers=headers,
        json=shift_payload(
            employee,
            obj,
            starts_at + timedelta(hours=1),
            starts_at + timedelta(hours=4),
        ),
    )
    assert overlap.status_code == 409
    assert overlap.json()["detail"]["conflicts"][0]["code"] == "time_overlap"

    rest_conflict = client.post(
        "/api/v1/scheduling/shifts",
        headers=headers,
        json=shift_payload(
            employee,
            obj,
            starts_at + timedelta(hours=9),
            starts_at + timedelta(hours=13),
        ),
    )
    assert rest_conflict.status_code == 409
    assert any(
        item["code"] == "minimum_rest" for item in rest_conflict.json()["detail"]["conflicts"]
    )

    published = client.post(
        f"/api/v1/scheduling/shifts/{shift['id']}/publish",
        headers=headers,
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    history = client.get(f"/api/v1/scheduling/shifts/{shift['id']}/history")
    assert history.status_code == 200
    assert [row["action"] for row in history.json()] == ["published", "updated", "created"]

    filtered = client.get(
        "/api/v1/scheduling/shifts",
        params={
            "from_date": starts_at.date().isoformat(),
            "to_date": starts_at.date().isoformat(),
            "employee_id": employee["id"],
            "object_id": obj["id"],
        },
    )
    assert filtered.status_code == 200
    assert [row["id"] for row in filtered.json()] == [shift["id"]]
    cancelled = client.post(
        f"/api/v1/scheduling/shifts/{shift['id']}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert (
        client.get(
            "/api/v1/scheduling/shifts",
            params={
                "from_date": starts_at.date().isoformat(),
                "to_date": starts_at.date().isoformat(),
            },
        ).json()
        == []
    )
    assert (
        len(
            client.get(
                "/api/v1/scheduling/shifts",
                params={
                    "from_date": starts_at.date().isoformat(),
                    "to_date": starts_at.date().isoformat(),
                    "include_cancelled": "true",
                },
            ).json()
        )
        == 1
    )


def test_qualification_absence_and_local_time_validation(client: TestClient) -> None:
    employee, obj, csrf = setup_schedule(client)
    headers = {"X-CSRF-Token": csrf}
    work_date = date.today() + timedelta(days=50)
    starts_at = datetime.combine(work_date, time(9))
    payload = shift_payload(employee, obj, starts_at, starts_at + timedelta(hours=8))
    payload["required_qualification"] = "Erste Hilfe"
    missing_qualification = client.post(
        "/api/v1/scheduling/shifts",
        headers=headers,
        json=payload,
    )
    assert missing_qualification.status_code == 409
    assert missing_qualification.json()["detail"]["conflicts"][0]["code"] == "qualification_missing"

    with TestingSessionLocal() as db:
        db.add(
            EmployeeQualification(
                employee_id=UUID(employee["id"]),
                category="Erste Hilfe",
                name="Erste Hilfe",
                valid_from=work_date - timedelta(days=1),
                expires_on=work_date + timedelta(days=30),
            )
        )
        db.commit()
    qualified_payload = shift_payload(
        employee,
        obj,
        datetime.combine(work_date + timedelta(days=10), time(9)),
        datetime.combine(work_date + timedelta(days=10), time(17)),
    )
    qualified_payload["required_qualification"] = "Erste Hilfe"
    qualified_shift = client.post(
        "/api/v1/scheduling/shifts",
        headers=headers,
        json=qualified_payload,
    )
    assert qualified_shift.status_code == 201, qualified_shift.text
    absence = client.post(
        f"/api/v1/employees/{employee['id']}/absences",
        headers=headers,
        json={
            "absence_type": "vacation",
            "starts_on": work_date.isoformat(),
            "ends_on": work_date.isoformat(),
            "status": "approved",
        },
    )
    assert absence.status_code == 201
    absent_employee = client.post("/api/v1/scheduling/shifts", headers=headers, json=payload)
    assert absent_employee.status_code == 409
    assert absent_employee.json()["detail"]["conflicts"][0]["code"] == "employee_absence"

    invalid_zone = client.patch(
        "/api/v1/scheduling/settings",
        headers=headers,
        json={"time_zone": "Not/A_Timezone", "minimum_rest_hours": 11},
    )
    assert invalid_zone.status_code == 422
    invalid_local_time = client.post(
        "/api/v1/scheduling/shifts",
        headers=headers,
        json=shift_payload(
            employee,
            obj,
            datetime(2027, 3, 28, 2, 30),
            datetime(2027, 3, 28, 4, 0),
        ),
    )
    assert invalid_local_time.status_code == 422
    assert "Zeitumstellung" in invalid_local_time.json()["detail"]
    first_occurrence = datetime(2027, 10, 31, 2, 30).replace(
        tzinfo=ZoneInfo("Europe/Berlin"),
        fold=0,
    )
    second_occurrence = first_occurrence.replace(fold=1)
    assert second_occurrence.astimezone(UTC) - first_occurrence.astimezone(UTC) == timedelta(
        hours=1
    )
    configured = client.patch(
        "/api/v1/scheduling/settings",
        headers=headers,
        json={"time_zone": "UTC", "minimum_rest_hours": 8},
    )
    assert configured.status_code == 200
    assert configured.json()["time_zone"] == "UTC"
    assert configured.json()["minimum_rest_hours"] == 8


def test_employee_must_be_assigned_to_the_scheduled_object(client: TestClient) -> None:
    employee, obj, csrf = setup_schedule(client)
    headers = {"X-CSRF-Token": csrf}
    removed = client.put(
        f"/api/v1/objects/{obj['id']}/assignments",
        headers=headers,
        json={"user_ids": []},
    )
    assert removed.status_code == 200
    starts_at = datetime.combine(date.today() + timedelta(days=80), time(9))
    conflict = client.post(
        "/api/v1/scheduling/shifts",
        headers=headers,
        json=shift_payload(employee, obj, starts_at, starts_at + timedelta(hours=8)),
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["conflicts"][0]["code"] == "object_assignment"


def test_schedule_permissions_are_checked_server_side(client: TestClient) -> None:
    setup_schedule(client)
    settings = client.get("/api/v1/scheduling/settings")
    assert settings.status_code == 200

    employee_csrf = sign_in(client, "dienstplan-person", "dienstplan-test-passwort-2026")
    denied = client.patch(
        "/api/v1/scheduling/settings",
        headers={"X-CSRF-Token": employee_csrf},
        json={"time_zone": "UTC", "minimum_rest_hours": 8},
    )
    assert denied.status_code == 403
    assert client.get("/api/v1/scheduling/shifts").status_code == 200

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": employee_csrf})
    assert client.get("/api/v1/scheduling/settings").status_code == 401


@pytest.mark.skipif(test_engine.dialect.name != "postgresql", reason="PostgreSQL-Constraint-Test")
def test_parallel_overlapping_inserts_are_rejected_by_postgresql(client: TestClient) -> None:
    employee, obj, _ = setup_schedule(client)
    employee_id = UUID(employee["id"])
    object_id = UUID(obj["id"])
    starts_at = datetime.now(UTC) + timedelta(days=60)
    barrier = Barrier(2)

    def insert_shift() -> str:
        with TestingSessionLocal() as db:
            db.add(
                ScheduleShift(
                    employee_id=employee_id,
                    object_id=object_id,
                    starts_at=starts_at,
                    ends_at=starts_at + timedelta(hours=4),
                    break_minutes=0,
                    status="draft",
                )
            )
            barrier.wait(timeout=10)
            try:
                db.commit()
            except (IntegrityError, OperationalError) as exc:
                if (
                    isinstance(exc, OperationalError)
                    and getattr(exc.orig, "sqlstate", None) != "40P01"
                ):
                    raise
                db.rollback()
                return "conflict"
            return "created"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: insert_shift(), range(2)))
    assert sorted(results) == ["conflict", "created"]
