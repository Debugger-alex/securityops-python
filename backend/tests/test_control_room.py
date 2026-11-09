from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.identity_api import password_hasher
from app.models import (
    BillingInvoice,
    Contract,
    Customer,
    Employee,
    EmployeeAbsence,
    EmployeeQualification,
    Incident,
    ObjectAssignment,
    OWKSEvent,
    OWKSEventStatus,
    Permission,
    Role,
    ScheduleShift,
    SecurityObject,
    Task,
    User,
)


def sign_in(client: TestClient, username: str = "admin", password: str = ADMIN_PASSWORD):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": client.cookies.get("securityops_csrf", "")}


def setup_control_room_scope() -> tuple[str, str, str]:
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "object_manager"))
        assert role is not None
        needed_codes = (
            "control_room.read",
            "objects.read",
            "scheduling.read",
            "employees.read",
            "employees.absences.read",
            "owks.read",
            "incidents.read",
            "tasks.read_own",
            "billing.invoices.read",
            "billing.invoices.approve",
        )
        permissions = {
            permission.code: permission
            for permission in db.scalars(
                select(Permission).where(Permission.code.in_(needed_codes))
            ).all()
        }
        role.permissions = [permissions[code] for code in needed_codes]
        user = User(
            username="control_room_operator",
            email="control_room_operator@example.com",
            full_name="Test Leitstellenzugriff",
            password_hash=password_hasher.hash("leitstelle-test-passwort-2026"),
            roles=[role],
        )
        customer_a = Customer(
            customer_number="K-CR-A",
            company_name="Testkunde Leitstelle A",
        )
        customer_b = Customer(
            customer_number="K-CR-B",
            company_name="Testkunde Leitstelle B",
        )
        db.add_all((user, customer_a, customer_b))
        db.flush()
        object_a = SecurityObject(
            customer_id=customer_a.id,
            code="CR-TEST-A",
            name="Testobjekt Leitstelle A",
        )
        object_b = SecurityObject(
            customer_id=customer_b.id,
            code="CR-TEST-B",
            name="Testobjekt Leitstelle B",
        )
        db.add_all((object_a, object_b))
        db.flush()
        db.add(ObjectAssignment(object_id=object_a.id, user_id=user.id))
        employee = Employee(
            employee_number="P-CR-TEST",
            user_id=user.id,
            full_name="Testbeschäftigte Leitstelle",
            hired_on=date.today() - timedelta(days=30),
        )
        db.add(employee)
        db.flush()
        now = datetime.now(UTC)
        db.add_all(
            (
                ScheduleShift(
                    employee_id=employee.id,
                    object_id=object_a.id,
                    starts_at=now - timedelta(hours=1),
                    ends_at=now + timedelta(hours=1),
                    status="published",
                ),
                ScheduleShift(
                    employee_id=employee.id,
                    object_id=object_b.id,
                    starts_at=now - timedelta(hours=1),
                    ends_at=now + timedelta(hours=1),
                    status="published",
                ),
                OWKSEvent(
                    object_id=object_a.id,
                    event_type="missed",
                    severity="warning",
                    title="Synthetische versäumte Kontrolle",
                    occurred_at=now,
                ),
                OWKSEvent(
                    object_id=object_a.id,
                    event_type="missed",
                    severity="warning",
                    title="Bereits erledigtes synthetisches Kontrollereignis",
                    occurred_at=now,
                ),
                OWKSEvent(
                    object_id=object_b.id,
                    event_type="missed",
                    severity="critical",
                    title="Fremdes synthetisches Kontrollereignis",
                    occurred_at=now,
                ),
                Incident(
                    title="Synthetischer offener Vorfall",
                    report="Testbericht ohne personenbezogene Daten.",
                    incident_type="incident",
                    severity="high",
                    object_id=object_a.id,
                    status="action_required",
                    due_at=now - timedelta(hours=1),
                    assigned_to_id=user.id,
                ),
                Incident(
                    title="Fremder synthetischer Vorfall",
                    report="Testbericht ohne personenbezogene Daten.",
                    incident_type="incident",
                    severity="critical",
                    object_id=object_b.id,
                    status="reported",
                    assigned_to_id=user.id,
                ),
                Task(
                    title="Synthetische dringende Aufgabe",
                    assigned_to_id=user.id,
                    object_id=object_a.id,
                    priority="urgent",
                    status="open",
                    due_at=now - timedelta(hours=1),
                ),
                Task(
                    title="Fremde synthetische Aufgabe",
                    assigned_to_id=user.id,
                    object_id=object_b.id,
                    priority="urgent",
                    status="open",
                    due_at=now - timedelta(hours=1),
                ),
                EmployeeAbsence(
                    employee_id=employee.id,
                    absence_type="vacation",
                    status="approved",
                    starts_on=date.today(),
                    ends_on=date.today() + timedelta(days=2),
                ),
                EmployeeQualification(
                    employee_id=employee.id,
                    category="Testqualifikation",
                    name="Synthetischer Nachweis",
                    expires_on=date.today() + timedelta(days=14),
                ),
            )
        )
        db.flush()
        object_a_contract = Contract(
            contract_number="CR-CONTRACT-A",
            name="Testvertrag Leitstelle A",
            contract_type="object",
            counterparty=customer_a.company_name,
            customer_id=customer_a.id,
            object_id=object_a.id,
            starts_on=date.today(),
        )
        object_b_contract = Contract(
            contract_number="CR-CONTRACT-B",
            name="Testvertrag Leitstelle B",
            contract_type="object",
            counterparty=customer_b.company_name,
            customer_id=customer_b.id,
            object_id=object_b.id,
            starts_on=date.today(),
        )
        db.add_all((object_a_contract, object_b_contract))
        db.flush()
        db.add_all(
            (
                BillingInvoice(
                    invoice_number="CR-INVOICE-A",
                    idempotency_key="control-room-invoice-a",
                    customer_id=customer_a.id,
                    contract_id=object_a_contract.id,
                    kind="invoice",
                    status="draft",
                    currency="EUR",
                    issued_on=date.today(),
                    due_on=date.today() + timedelta(days=30),
                    customer_snapshot={"name": customer_a.company_name},
                    inputs_snapshot={},
                    net_amount=Decimal("100.00"),
                    tax_amount=Decimal("19.00"),
                    gross_amount=Decimal("119.00"),
                ),
                BillingInvoice(
                    invoice_number="CR-INVOICE-B",
                    idempotency_key="control-room-invoice-b",
                    customer_id=customer_b.id,
                    contract_id=object_b_contract.id,
                    kind="invoice",
                    status="draft",
                    currency="EUR",
                    issued_on=date.today(),
                    due_on=date.today() + timedelta(days=30),
                    customer_snapshot={"name": customer_b.company_name},
                    inputs_snapshot={},
                    net_amount=Decimal("100.00"),
                    tax_amount=Decimal("19.00"),
                    gross_amount=Decimal("119.00"),
                ),
            )
        )
        db.flush()
        active_event = db.scalar(
            select(OWKSEvent).where(OWKSEvent.title == "Synthetische versäumte Kontrolle")
        )
        assert active_event is not None
        resolved_event = db.scalar(
            select(OWKSEvent).where(
                OWKSEvent.title == "Bereits erledigtes synthetisches Kontrollereignis"
            )
        )
        assert resolved_event is not None
        db.add(
            OWKSEventStatus(
                event_id=active_event.id,
                sequence_no=1,
                status="open",
                note="",
            )
        )
        db.add(
            OWKSEventStatus(
                event_id=resolved_event.id,
                sequence_no=1,
                status="resolved",
                note="",
            )
        )
        db.commit()
        return str(user.id), str(object_a.id), str(object_b.id)


def test_control_room_uses_real_sources_and_scopes_every_source_to_assignment(
    client: TestClient,
) -> None:
    user_id, object_a_id, object_b_id = setup_control_room_scope()
    headers = sign_in(client, "control_room_operator", "leitstelle-test-passwort-2026")
    response = client.get(
        "/api/v1/control-room",
        headers=headers,
        params={
            "object_id": object_a_id,
            "from_date": str(date.today() - timedelta(days=1)),
            "to_date": str(date.today() + timedelta(days=30)),
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["counts"]["active_objects"] == 1
    assert payload["counts"]["active_shifts"] == 1
    assert payload["counts"]["open_owks_events"] == 1
    assert payload["counts"]["open_incidents"] == 1
    assert payload["counts"]["overdue_incidents"] == 1
    assert payload["counts"]["open_tasks"] == 1
    assert payload["counts"]["urgent_tasks"] == 1
    assert payload["counts"]["active_absences"] == 1
    assert payload["counts"]["qualification_problems"] == 1
    assert payload["counts"]["billing_approvals"] == 1
    assert payload["shifts"][0]["employee_name"] == "Testbeschäftigte Leitstelle"
    assert payload["incidents"][0]["title"] == "Synthetischer offener Vorfall"
    assert "report" not in payload["incidents"][0]
    assert payload["tasks"][0]["assigned_to_name"] == "Test Leitstellenzugriff"
    assert payload["billing_approvals"][0]["invoice_number"] == "CR-INVOICE-A"
    serialized = response.text
    assert object_b_id not in serialized
    assert "Fremdes synthetisches" not in serialized
    assert "Testbericht ohne personenbezogene Daten." not in serialized
    assert user_id not in serialized

    assert (
        client.get(
            "/api/v1/control-room",
            headers=headers,
            params={"object_id": object_b_id},
        ).status_code
        == 404
    )


def test_control_room_requires_permission_and_omits_unavailable_sources(client: TestClient) -> None:
    denied = User(
        username="control_room_denied",
        email="control_room_denied@example.com",
        full_name="Test ohne Leitstellenrecht",
        password_hash=password_hasher.hash("leitstelle-test-passwort-2026"),
        roles=[],
    )
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "employee"))
        assert role is not None
        denied.roles = [role]
        db.add(denied)
        db.commit()

    headers = sign_in(client, "control_room_denied", "leitstelle-test-passwort-2026")
    assert client.get("/api/v1/control-room", headers=headers).status_code == 403

    _, object_a_id, _ = setup_control_room_scope()
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "object_manager"))
        assert role is not None
        object_permission = db.scalar(select(Permission).where(Permission.code == "objects.read"))
        control_room_permission = db.scalar(
            select(Permission).where(Permission.code == "control_room.read")
        )
        assert object_permission is not None and control_room_permission is not None
        role.permissions = [object_permission, control_room_permission]
        db.commit()
    scoped_headers = sign_in(client, "control_room_operator", "leitstelle-test-passwort-2026")
    response = client.get(
        "/api/v1/control-room",
        headers=scoped_headers,
        params={"object_id": object_a_id},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["objects"]
    assert "shifts" not in payload
    assert "owks_events" not in payload
    assert "incidents" not in payload
    assert "tasks" not in payload
    assert "absences" not in payload
    assert "qualifications" not in payload
    assert "billing_approvals" not in payload


def test_control_room_applies_date_range_to_events_and_absences(client: TestClient) -> None:
    _, object_a_id, _ = setup_control_room_scope()
    headers = sign_in(client, "control_room_operator", "leitstelle-test-passwort-2026")
    response = client.get(
        "/api/v1/control-room",
        headers=headers,
        params={
            "object_id": object_a_id,
            "from_date": str(date.today() + timedelta(days=3)),
            "to_date": str(date.today() + timedelta(days=30)),
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["counts"]["open_owks_events"] == 0
    assert payload["counts"]["active_absences"] == 0
    assert payload["counts"]["active_shifts"] == 1
    assert payload["counts"]["open_incidents"] == 1
    assert payload["counts"]["open_tasks"] == 1
