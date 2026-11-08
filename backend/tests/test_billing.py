from datetime import UTC, datetime, timedelta
from uuid import UUID

from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient
from sqlalchemy import select
from test_time_tracking import setup_tracking

from app.models import (
    AuditLog,
    BillingInvoice,
    BillingInvoiceLine,
    TimeEntry,
    TimeEntrySegment,
)


def sign_in(client: TestClient, username: str = "admin", password: str = ADMIN_PASSWORD):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": client.cookies.get("securityops_csrf", "")}


def create_invoice(client: TestClient, headers: dict[str, str]):
    customer = client.post("/api/v1/customers", headers=headers, json={"company_name": "Testkunde"})
    assert customer.status_code == 201, customer.text
    rate = client.post(
        "/api/v1/billing/rates",
        headers=headers,
        json={
            "code": "STD-TEST",
            "name": "Testleistung",
            "kind": "hourly",
            "unit": "Stunde",
            "unit_price": "0.05",
            "tax_code": "TEST",
            "tax_rate": "10",
        },
    )
    assert rate.status_code == 201, rate.text
    response = client.post(
        "/api/v1/billing/invoices",
        headers=headers,
        json={
            "idempotency_key": "invoice-test-key-001",
            "customer_id": customer.json()["id"],
            "issued_on": "2026-11-08",
            "due_on": "2026-12-08",
            "lines": [{"rate_id": rate.json()["id"], "quantity": "1"}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_invoice_rounding_state_machine_correction_and_export(client: TestClient):
    headers = sign_in(client)
    invoice = create_invoice(client, headers)
    assert invoice["net_amount"] == "0.05"
    assert invoice["tax_amount"] == "0.01"
    assert invoice["gross_amount"] == "0.06"
    assert invoice["lines"][0]["tax_code"] == "TEST"
    assert client.get(f"/api/v1/billing/invoices/{invoice['id']}/pdf").status_code == 409

    repeated = client.post(
        "/api/v1/billing/invoices",
        headers=headers,
        json={
            "idempotency_key": "invoice-test-key-001",
            "customer_id": invoice["customer_id"],
            "issued_on": "2026-11-08",
            "due_on": "2026-12-08",
            "lines": [{"rate_id": invoice["lines"][0]["id"], "quantity": "1"}],
        },
    )
    assert repeated.status_code == 409

    approved = client.post(f"/api/v1/billing/invoices/{invoice['id']}/approve", headers=headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert (
        client.post(
            f"/api/v1/billing/invoices/{invoice['id']}/approve", headers=headers
        ).status_code
        == 409
    )
    pdf = client.get(f"/api/v1/billing/invoices/{invoice['id']}/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-1.4")
    assert pdf.headers["cache-control"] == "private, no-store"
    assert pdf.headers["x-content-type-options"] == "nosniff"

    correction = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/corrections",
        headers=headers,
        json={
            "idempotency_key": "correction-test-001",
            "reason": "Nachvollziehbarer Korrekturtest",
            "issued_on": "2026-11-09",
            "due_on": "2026-12-09",
        },
    )
    assert correction.status_code == 201, correction.text
    assert correction.json()["correction_of_id"] == invoice["id"]
    assert correction.json()["kind"] == "cancellation"
    assert correction.json()["gross_amount"] == "-0.06"
    assert (
        client.post(
            f"/api/v1/billing/invoices/{invoice['id']}/archive",
            headers=headers,
            json={"reason": "Archivtest"},
        ).status_code
        == 200
    )

    exported = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/exports",
        headers=headers,
        params={"idempotency_key": "export-test-key-001"},
    )
    assert exported.status_code == 201, exported.text
    assert exported.json()["payload"]["schema_version"] == "securityops-accounting-v1"
    assert len(exported.json()["payload_sha256"]) == 64
    duplicate_export = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/exports",
        headers=headers,
        params={"idempotency_key": "export-test-key-001"},
    )
    assert duplicate_export.status_code == 201
    assert duplicate_export.json()["id"] == exported.json()["id"]

    payment = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/payments",
        headers=headers,
        json={
            "idempotency_key": "payment-test-001",
            "amount": "0.06",
            "paid_on": "2026-11-09",
        },
    )
    assert payment.status_code == 201, payment.text
    listing = client.get("/api/v1/billing/invoices", headers=headers).json()
    assert next(item for item in listing if item["id"] == invoice["id"])["payment_status"] == "paid"
    with TestingSessionLocal() as db:
        stored = db.scalar(select(BillingInvoice).where(BillingInvoice.id == UUID(invoice["id"])))
        assert stored is not None
        assert (
            db.scalar(
                select(BillingInvoiceLine).where(
                    BillingInvoiceLine.invoice_id == UUID(correction.json()["id"])
                )
            ).unit_price
            < 0
        )
        assert (
            db.scalar(
                select(AuditLog).where(
                    AuditLog.entity_type == "billing_invoice",
                    AuditLog.entity_id == invoice["id"],
                    AuditLog.action == "billing.invoice.approved",
                )
            )
            is not None
        )


def test_billing_routes_require_finance_permissions(client: TestClient):
    headers = sign_in(client, "geschaeftsfuehrung", "management-test-passwort-2026")
    assert client.get("/api/v1/billing/invoices", headers=headers).status_code == 403
    employee_headers = sign_in(client, "admin")
    client.post("/api/v1/auth/logout", headers=employee_headers)


def test_invoice_uses_approved_time_snapshot_and_prevents_double_billing(client: TestClient):
    employee, obj, csrf = setup_tracking(client, "Testkunde Rechnungswesen Zeit")
    start = datetime.now(UTC) - timedelta(hours=3)
    end = start + timedelta(minutes=90)
    with TestingSessionLocal() as db:
        entry = TimeEntry(
            employee_id=UUID(employee["id"]),
            object_id=UUID(obj["id"]),
            started_at=start,
            ended_at=end,
            status="approved",
            segments=[
                TimeEntrySegment(
                    position=1,
                    kind="work",
                    started_at=start,
                    ended_at=end,
                )
            ],
        )
        db.add(entry)
        db.commit()
        entry_id = entry.id

    rate = client.post(
        "/api/v1/billing/rates",
        headers={"X-CSRF-Token": csrf},
        json={
            "code": "TIME-TEST",
            "name": "Freigegebene Arbeitszeit",
            "kind": "hourly",
            "unit": "Stunde",
            "unit_price": "80",
            "tax_code": "TEST",
            "tax_rate": "0",
        },
    )
    assert rate.status_code == 201, rate.text
    response = client.post(
        "/api/v1/billing/invoices",
        headers={"X-CSRF-Token": csrf},
        json={
            "idempotency_key": "time-invoice-test-001",
            "customer_id": obj["customer_id"],
            "issued_on": "2026-11-08",
            "due_on": "2026-12-08",
            "lines": [
                {
                    "rate_id": rate.json()["id"],
                    "quantity": "99",
                    "source_time_entry_ids": [str(entry_id)],
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    invoice = response.json()
    assert invoice["lines"][0]["quantity"] == "1.5000"
    assert invoice["net_amount"] == "120.00"
    with TestingSessionLocal() as db:
        stored = db.scalar(select(BillingInvoice).where(BillingInvoice.id == UUID(invoice["id"])))
        assert stored is not None
        assert stored.inputs_snapshot["source_time_entries"][0]["time_entry_id"] == str(entry_id)
        assert len(stored.inputs_snapshot["source_time_entries"][0]["segments"]) == 1

    duplicate = client.post(
        "/api/v1/billing/invoices",
        headers={"X-CSRF-Token": csrf},
        json={
            "idempotency_key": "time-invoice-test-002",
            "customer_id": obj["customer_id"],
            "issued_on": "2026-11-08",
            "due_on": "2026-12-08",
            "lines": [
                {
                    "rate_id": rate.json()["id"],
                    "quantity": "1",
                    "source_time_entry_ids": [str(entry_id)],
                }
            ],
        },
    )
    assert duplicate.status_code == 409
