from uuid import UUID

from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.identity_api import password_hasher
from app.models import (
    AuditLog,
    ObjectAssignment,
    Role,
    SecurityObject,
    User,
)


def sign_in(client: TestClient, username: str = "admin", password: str = ADMIN_PASSWORD):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": client.cookies.get("securityops_csrf", "")}


def create_object(client: TestClient, headers: dict[str, str], code: str) -> tuple[str, str]:
    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": f"Testkunde {code}"},
    )
    assert customer_response.status_code == 201
    object_response = client.post(
        "/api/v1/objects",
        headers=headers,
        json={
            "customer_id": customer_response.json()["id"],
            "name": f"Testobjekt {code}",
            "code": code,
        },
    )
    assert object_response.status_code == 201
    return customer_response.json()["id"], object_response.json()["id"]


def create_assigned_employee(object_id: str) -> str:
    with TestingSessionLocal() as db:
        role = db.scalar(select(Role).where(Role.code == "employee"))
        security_object = db.get(SecurityObject, UUID(object_id))
        assert role is not None and security_object is not None
        user = User(
            username="task_employee",
            email="task_employee@example.com",
            full_name="Test Mitarbeiter",
            password_hash=password_hasher.hash("task-test-passwort-2026"),
            roles=[role],
        )
        db.add(user)
        db.flush()
        db.add(ObjectAssignment(object_id=security_object.id, user_id=user.id))
        db.commit()
        return str(user.id)


def test_task_lifecycle_comments_completion_and_audit(client: TestClient) -> None:
    headers = sign_in(client)
    with TestingSessionLocal() as db:
        assignee_id = db.scalar(select(User.id).where(User.username == "geschaeftsfuehrung"))
        admin_id = db.scalar(select(User.id).where(User.username == "admin"))
    assert assignee_id is not None and admin_id is not None
    response = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Kontrollbericht prüfen",
            "description": "Ergebnis nachvollziehbar dokumentieren",
            "due_at": "2026-12-01T10:00:00+01:00",
            "priority": "high",
            "assigned_to_id": str(assignee_id),
        },
    )
    assert response.status_code == 201, response.text
    task = response.json()
    assert task["assigned_to_name"] == "Test Geschäftsführung"
    assert task["status"] == "open"
    assert task["due_at"].endswith("Z")

    null_title = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"title": None},
    )
    assert null_title.status_code == 422

    reassigned = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"assigned_to_id": str(admin_id)},
    )
    assert reassigned.status_code == 200, reassigned.text
    assert reassigned.json()["assigned_to_id"] == str(admin_id)
    assert reassigned.json()["assigned_to_name"] == "Test Administration"

    missing_proof = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"status": "completed"},
    )
    assert missing_proof.status_code == 422
    assert "Erledigungsnachweis" in missing_proof.json()["detail"]

    comment = client.post(
        f"/api/v1/tasks/{task['id']}/comments",
        headers=headers,
        json={"body": "Prüfung wurde begonnen."},
    )
    assert comment.status_code == 201, comment.text
    completed = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"status": "completed", "completion_evidence": "Bericht geprüft und abgelegt."},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["completion_evidence"] == "Bericht geprüft und abgelegt."

    detail = client.get(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert detail.status_code == 200
    assert [item["body"] for item in detail.json()["comments"]] == ["Prüfung wurde begonnen."]
    assert {item["action"] for item in detail.json()["history"]} == {
        "created",
        "assigned",
        "updated",
        "comment_added",
        "completed",
    }
    with TestingSessionLocal() as db:
        audit_actions = set(
            db.scalars(
                select(AuditLog.action).where(
                    AuditLog.entity_type == "task",
                    AuditLog.entity_id == task["id"],
                )
            ).all()
        )
    assert {
        "task.created",
        "task.updated",
        "task.assigned",
        "task.completed",
        "task.comment_added",
    } <= audit_actions


def test_task_visibility_is_limited_to_own_and_assigned_object_scope(client: TestClient) -> None:
    admin_headers = sign_in(client)
    _, object_id = create_object(client, admin_headers, "TASK-001")
    _, other_object_id = create_object(client, admin_headers, "TASK-002")
    create_assigned_employee(object_id)

    object_task = client.post(
        "/api/v1/tasks",
        headers=admin_headers,
        json={
            "title": "Objektbezogene Aufgabe",
            "object_id": object_id,
            "assigned_to_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert object_task.status_code == 422
    object_task = client.post(
        "/api/v1/tasks",
        headers=admin_headers,
        json={"title": "Objektbezogene Aufgabe", "object_id": object_id},
    )
    assert object_task.status_code == 201, object_task.text
    other_task = client.post(
        "/api/v1/tasks",
        headers=admin_headers,
        json={"title": "Nicht zugewiesene Aufgabe"},
    )
    assert other_task.status_code == 201
    foreign_object_task = client.post(
        "/api/v1/tasks",
        headers=admin_headers,
        json={"title": "Andere Objektaufgabe", "object_id": other_object_id},
    )
    assert foreign_object_task.status_code == 201

    employee_headers = sign_in(client, "task_employee", "task-test-passwort-2026")
    page = client.get("/api/v1/tasks", headers=employee_headers)
    assert page.status_code == 200
    assert [item["id"] for item in page.json()["items"]] == [object_task.json()["id"]]
    assert (
        client.get(
            f"/api/v1/tasks/{object_task.json()['id']}", headers=employee_headers
        ).status_code
        == 200
    )
    scoped_update = client.patch(
        f"/api/v1/tasks/{object_task.json()['id']}",
        headers=employee_headers,
        json={"description": "Nur im zugewiesenen Objektbereich geändert."},
    )
    assert scoped_update.status_code == 200, scoped_update.text
    for task in (other_task.json(), foreign_object_task.json()):
        assert (
            client.get(f"/api/v1/tasks/{task['id']}", headers=employee_headers).status_code == 404
        )
        assert (
            client.patch(
                f"/api/v1/tasks/{task['id']}",
                headers=employee_headers,
                json={"title": "Fremder Zugriff"},
            ).status_code
            == 404
        )


def test_task_creation_enforces_object_assignment_and_customer_consistency(
    client: TestClient,
) -> None:
    admin_headers = sign_in(client)
    customer_id, object_id = create_object(client, admin_headers, "TASK-003")
    other_customer_id, _ = create_object(client, admin_headers, "TASK-004")
    create_assigned_employee(object_id)

    employee_headers = sign_in(client, "task_employee", "task-test-passwort-2026")
    denied = client.post(
        "/api/v1/tasks",
        headers=employee_headers,
        json={"title": "Fremdes Objekt", "object_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert denied.status_code == 404

    mismatch = client.post(
        "/api/v1/tasks",
        headers=employee_headers,
        json={
            "title": "Unstimmiger Bezug",
            "customer_id": other_customer_id,
            "object_id": object_id,
        },
    )
    assert mismatch.status_code == 422

    valid = client.post(
        "/api/v1/tasks",
        headers=employee_headers,
        json={"title": "Zugewiesenes Objekt", "object_id": object_id},
    )
    assert valid.status_code == 201, valid.text
    assert valid.json()["customer_id"] == customer_id


def test_tasks_require_explicit_permission_and_validate_filters(client: TestClient) -> None:
    with TestingSessionLocal() as db:
        role = Role(
            code="taskless_test",
            name="Ohne Aufgabenrechte",
            description="Testrolle ohne Aufgabenrechte",
        )
        user = User(
            username="taskless",
            email="taskless@example.com",
            full_name="Test Ohne Aufgabenrechte",
            password_hash=password_hasher.hash("task-test-passwort-2026"),
            roles=[role],
        )
        db.add(user)
        db.commit()

    headers = sign_in(client, "taskless", "task-test-passwort-2026")
    assert client.get("/api/v1/tasks", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/v1/tasks",
            headers=headers,
            json={"title": "Nicht erlaubt"},
        ).status_code
        == 403
    )
    admin_headers = sign_in(client)
    assert client.get("/api/v1/tasks?limit=101", headers=admin_headers).status_code == 422
    assert (
        client.post(
            "/api/v1/tasks",
            headers=admin_headers,
            json={"title": "   "},
        ).status_code
        == 422
    )
