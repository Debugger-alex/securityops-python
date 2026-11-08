from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from conftest import TestingSessionLocal
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.identity_api import password_hasher
from app.models import (
    Permission,
    Role,
    TimeEntry,
    TimeEntrySegment,
    User,
)

EMPLOYEE_PASSWORD = "zeiterfassung-test-passwort-2026"


def sign_in(
    client: TestClient, username: str = "admin", password: str = "sicheres-test-passwort-2026"
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return client.cookies.get("securityops_csrf", "")


def setup_tracking(client: TestClient, customer_name: str = "Testkunde Zeiterfassung"):
    admin_headers = {"X-CSRF-Token": sign_in(client)}
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "employee"))
        assert role is not None
        user = User(
            username="zeiterfassung-person",
            email="zeiterfassung-person@example.com",
            full_name="Testperson Zeiterfassung",
            password_hash=password_hasher.hash(EMPLOYEE_PASSWORD),
            roles=[role],
        )
        db.add(user)
        db.commit()
        user_id = user.id

    employee_response = client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={
            "employee_number": "P-TIME-001",
            "user_id": str(user_id),
            "full_name": "Testperson Zeiterfassung",
            "hired_on": str(date.today() - timedelta(days=100)),
        },
    )
    assert employee_response.status_code == 201, employee_response.text
    employee = employee_response.json()
    customer_response = client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"company_name": customer_name},
    )
    assert customer_response.status_code == 201, customer_response.text
    object_response = client.post(
        "/api/v1/objects",
        headers=admin_headers,
        json={
            "customer_id": customer_response.json()["id"],
            "name": "Testobjekt Zeiterfassung",
            "code": "OBJ-TIME-001",
        },
    )
    assert object_response.status_code == 201, object_response.text
    obj = object_response.json()
    assignment = client.put(
        f"/api/v1/objects/{obj['id']}/assignments",
        headers=admin_headers,
        json={"user_ids": [str(user_id)]},
    )
    assert assignment.status_code == 200, assignment.text
    return employee, obj, admin_headers["X-CSRF-Token"]


def create_published_shift(client: TestClient, employee: dict, obj: dict, csrf: str) -> dict:
    now = datetime.now(ZoneInfo("Europe/Berlin")).replace(second=0, microsecond=0)
    starts_at = (now - timedelta(hours=1)).replace(tzinfo=None)
    ends_at = (now + timedelta(hours=5)).replace(tzinfo=None)
    payload = {
        "employee_id": employee["id"],
        "object_id": obj["id"],
        "starts_at_local": starts_at.isoformat(timespec="minutes"),
        "ends_at_local": ends_at.isoformat(timespec="minutes"),
        "break_minutes": 30,
    }
    created = client.post(
        "/api/v1/scheduling/shifts",
        headers={"X-CSRF-Token": csrf},
        json=payload,
    )
    assert created.status_code == 201, created.text
    shift = created.json()
    published = client.post(
        f"/api/v1/scheduling/shifts/{shift['id']}/publish",
        headers={"X-CSRF-Token": csrf},
    )
    assert published.status_code == 200, published.text
    return published.json()


def test_tracking_segments_permissions_approval_and_immutable_correction(
    client: TestClient,
) -> None:
    employee, obj, admin_csrf = setup_tracking(client)
    shift = create_published_shift(client, employee, obj, admin_csrf)
    local_start = (
        datetime.fromisoformat(shift["starts_at"]).astimezone(ZoneInfo("Europe/Berlin")).date()
    )
    local_end = (
        datetime.fromisoformat(shift["ends_at"]).astimezone(ZoneInfo("Europe/Berlin")).date()
    )
    missing = client.get(
        "/api/v1/time-tracking/reports/missing",
        params={"from_date": local_start.isoformat(), "to_date": local_end.isoformat()},
    )
    assert missing.status_code == 200
    assert [row["shift_id"] for row in missing.json()] == [shift["id"]]
    with TestingSessionLocal() as db:
        employee_role = db.scalar(select(Role).where(Role.code == "employee"))
        approval_permission = db.scalar(
            select(Permission).where(Permission.code == "time_tracking.approve")
        )
        assert employee_role is not None
        assert approval_permission is not None
        employee_role.permissions.append(approval_permission)
        db.commit()
    employee_csrf = sign_in(client, "zeiterfassung-person", EMPLOYEE_PASSWORD)
    employee_headers = {"X-CSRF-Token": employee_csrf}

    started = client.post(
        "/api/v1/time-tracking/start",
        headers=employee_headers,
        json={"shift_id": shift["id"]},
    )
    assert started.status_code == 201, started.text
    entry = started.json()
    assert entry["status"] == "open"
    assert entry["shift_id"] == shift["id"]
    assert entry["planned_break_seconds"] == 1800
    assert entry["segments"][0]["kind"] == "work"

    invalid_resume = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/resume",
        headers=employee_headers,
    )
    assert invalid_resume.status_code == 409

    paused = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/pause",
        headers=employee_headers,
    )
    assert paused.status_code == 200, paused.text
    assert paused.json()["segments"][-1]["kind"] == "break"
    assert paused.json()["segments"][-1]["ended_at"] is None

    resumed = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/resume",
        headers=employee_headers,
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["segments"][-1]["kind"] == "work"

    submitted = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/stop",
        headers=employee_headers,
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "submitted"
    assert len(submitted.json()["segments"]) == 3
    assert submitted.json()["actual_work_seconds"] > 0

    self_approval = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/approve",
        headers=employee_headers,
    )
    assert self_approval.status_code == 403
    admin_csrf = sign_in(client)
    approved = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/approve",
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    original_start = approved.json()["segments"][0]["started_at"]

    employee_csrf = sign_in(client, "zeiterfassung-person", EMPLOYEE_PASSWORD)
    invalid_transition = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/stop",
        headers={"X-CSRF-Token": employee_csrf},
    )
    assert invalid_transition.status_code == 409

    correction_segments = [
        {
            "kind": segment["kind"],
            "started_at": segment["started_at"],
            "ended_at": segment["ended_at"],
        }
        for segment in approved.json()["segments"]
    ]
    correction_segments[0]["started_at"] = (
        datetime.fromisoformat(correction_segments[0]["started_at"]) - timedelta(minutes=1)
    ).isoformat()
    correction_segments[-1]["ended_at"] = (
        datetime.fromisoformat(correction_segments[-1]["ended_at"]) + timedelta(minutes=1)
    ).isoformat()
    requested = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/corrections",
        headers={"X-CSRF-Token": employee_csrf},
        json={"reason": "Vergessene Minuten ergänzt", "segments": correction_segments},
    )
    assert requested.status_code == 201, requested.text
    assert requested.json()["status"] == "pending"

    approved_correction = client.post(
        f"/api/v1/time-tracking/corrections/{requested.json()['id']}/approve",
        headers={"X-CSRF-Token": sign_in(client)},
    )
    assert approved_correction.status_code == 200, approved_correction.text
    assert approved_correction.json()["status"] == "approved"
    assert approved_correction.json()["started_at"] != original_start
    assert approved_correction.json()["corrections"][0]["status"] == "approved"

    with TestingSessionLocal() as db:
        original_segment = db.scalar(
            select(TimeEntrySegment)
            .where(TimeEntrySegment.entry_id == UUID(entry["id"]))
            .order_by(TimeEntrySegment.position)
            .limit(1)
        )
        assert original_segment is not None
        original_stored_start = original_segment.started_at
        if original_stored_start.tzinfo is None:
            original_stored_start = original_stored_start.replace(tzinfo=UTC)
        expected_original_start = datetime.fromisoformat(original_start)
        assert original_stored_start == expected_original_start
        stored_entry = db.get(TimeEntry, UUID(entry["id"]))
        assert stored_entry is not None
        assert stored_entry.status == "approved"


def test_manual_dst_entry_overlap_and_formula_safe_approved_export(client: TestClient) -> None:
    employee, obj, admin_csrf = setup_tracking(client, customer_name='=HYPERLINK("bad")')
    start = datetime(2027, 10, 31, 2, 15, tzinfo=ZoneInfo("Europe/Berlin"), fold=0)
    end = datetime(2027, 10, 31, 2, 15, tzinfo=ZoneInfo("Europe/Berlin"), fold=1)
    payload = {
        "employee_id": employee["id"],
        "object_id": obj["id"],
        "segments": [
            {"kind": "work", "started_at": start.isoformat(), "ended_at": end.isoformat()},
        ],
    }
    created = client.post(
        "/api/v1/time-tracking/entries/manual",
        headers={"X-CSRF-Token": admin_csrf},
        json=payload,
    )
    assert created.status_code == 201, created.text
    entry = created.json()
    assert entry["status"] == "submitted"
    assert entry["actual_work_seconds"] == 3600
    assert entry["time_zone"] == "Europe/Berlin"

    overlap = client.post(
        "/api/v1/time-tracking/entries/manual",
        headers={"X-CSRF-Token": admin_csrf},
        json=payload,
    )
    assert overlap.status_code == 409

    approved = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/approve",
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert approved.status_code == 200, approved.text
    export = client.get(
        "/api/v1/time-tracking/export.csv",
        params={"from_date": "2027-10-31", "to_date": "2027-10-31"},
    )
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "'=HYPERLINK" in export.text

    report = client.get(
        "/api/v1/time-tracking/reports",
        params={"from_date": "2027-10-31", "to_date": "2027-10-31", "group_by": "month"},
    )
    assert report.status_code == 200, report.text
    assert report.json()["actual_work_seconds"] == 3600
    assert report.json()["entry_count"] == 1
    assert report.json()["groups"][0]["label"] == "2027-10"

    corrected_segments = [
        {
            "kind": segment["kind"],
            "started_at": (
                datetime.fromisoformat(segment["started_at"]) - timedelta(days=1)
            ).isoformat(),
            "ended_at": (
                datetime.fromisoformat(segment["ended_at"]) - timedelta(days=1)
            ).isoformat(),
        }
        for segment in approved.json()["segments"]
    ]
    correction = client.post(
        f"/api/v1/time-tracking/entries/{entry['id']}/corrections",
        headers={"X-CSRF-Token": admin_csrf},
        json={
            "reason": "Korrektur auf den tatsächlichen Kalendertag",
            "segments": corrected_segments,
        },
    )
    assert correction.status_code == 201, correction.text
    correction_approval = client.post(
        f"/api/v1/time-tracking/corrections/{correction.json()['id']}/approve",
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert correction_approval.status_code == 200, correction_approval.text
    assert correction_approval.json()["started_at"].startswith("2027-10-30")
    corrected_report = client.get(
        "/api/v1/time-tracking/reports",
        params={"from_date": "2027-10-30", "to_date": "2027-10-30"},
    )
    assert corrected_report.status_code == 200, corrected_report.text
    assert corrected_report.json()["entry_count"] == 1
    assert corrected_report.json()["actual_work_seconds"] == 3600

    next_start = datetime(2027, 10, 31, 5, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    next_end = next_start + timedelta(hours=1)
    rejected_payload = {
        **payload,
        "segments": [
            {
                "kind": "work",
                "started_at": next_start.isoformat(),
                "ended_at": next_end.isoformat(),
            }
        ],
    }
    rejected_entry = client.post(
        "/api/v1/time-tracking/entries/manual",
        headers={"X-CSRF-Token": admin_csrf},
        json=rejected_payload,
    )
    assert rejected_entry.status_code == 201, rejected_entry.text
    missing_reason = client.post(
        f"/api/v1/time-tracking/entries/{rejected_entry.json()['id']}/reject",
        headers={"X-CSRF-Token": admin_csrf},
        json={},
    )
    assert missing_reason.status_code == 422
    rejected = client.post(
        f"/api/v1/time-tracking/entries/{rejected_entry.json()['id']}/reject",
        headers={"X-CSRF-Token": admin_csrf},
        json={"reason": "Buchung passt nicht zum Dienstnachweis"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"
