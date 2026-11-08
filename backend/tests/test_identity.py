from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient

from app.identity_api import password_hasher
from app.models import Role, User


def test_login_session_csrf_and_logout(client: TestClient) -> None:
    assert client.get("/api/v1/customers").status_code == 401

    failed = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "falsches-passwort"},
    )
    assert failed.status_code == 401
    assert failed.json()["detail"] == "Benutzername oder Passwort ist ungültig"

    signed_in = client.post(
        "/api/v1/auth/login",
        json={"username": "ADMIN", "password": ADMIN_PASSWORD},
    )
    assert signed_in.status_code == 200
    assert signed_in.json()["user"]["username"] == "admin"
    session_cookie = signed_in.cookies.get("securityops_session")
    csrf_cookie = signed_in.cookies.get("securityops_csrf")
    assert session_cookie and csrf_cookie
    set_cookie = signed_in.headers.get_list("set-cookie")
    assert any("securityops_session=" in value and "HttpOnly" in value for value in set_cookie)
    assert any(
        "securityops_session=" in value and "SameSite=strict" in value for value in set_cookie
    )
    assert "password_hash" not in signed_in.text

    assert client.get("/api/v1/auth/me").status_code == 200
    assert (
        client.post(
            "/api/v1/customers",
            json={"company_name": "Ohne CSRF"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf_cookie},
        ).status_code
        == 204
    )
    assert client.get("/api/v1/auth/me").status_code == 401


def test_rbac_and_user_administration(client: TestClient) -> None:
    csrf = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    ).cookies.get("securityops_csrf", "")
    headers = {"X-CSRF-Token": csrf}

    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "operator",
            "email": "operator@example.com",
            "full_name": "Operative Person",
            "password": "langes-testpasswort-2026",
            "role_codes": ["employee"],
        },
    )
    assert created.status_code == 201
    assert "password_hash" not in created.json()
    assert created.json()["roles"] == ["employee"]
    assert "customers.read" not in created.json()["permissions"]
    assert client.get("/api/v1/roles").status_code == 200
    assert client.get("/api/v1/audit-logs").status_code == 200
    own_id = client.get("/api/v1/auth/me").json()["user"]["id"]
    assert (
        client.patch(
            f"/api/v1/users/{own_id}",
            headers=headers,
            json={"is_active": False},
        ).status_code
        == 409
    )

    client.post(
        "/api/v1/auth/logout",
        headers=headers,
    )
    member_login = client.post(
        "/api/v1/auth/login",
        json={"username": "operator", "password": "langes-testpasswort-2026"},
    )
    assert member_login.status_code == 200
    assert client.get("/api/v1/customers").status_code == 403
    assert client.get("/api/v1/roles").status_code == 403

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    admin_csrf = admin_login.cookies.get("securityops_csrf", "")
    assert (
        client.patch(
            f"/api/v1/users/{created.json()['id']}",
            headers={"X-CSRF-Token": admin_csrf},
            json={"is_active": False},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "operator", "password": "langes-testpasswort-2026"},
        ).status_code
        == 401
    )


def test_employee_role_is_restricted_to_assigned_permissions(client: TestClient) -> None:
    with TestingSessionLocal() as db:
        role = db.query(Role).filter_by(code="employee").one_or_none()
        assert role is not None
        db.add(
            User(
                username="mitarbeiter",
                email="mitarbeiter@example.com",
                full_name="Test Mitarbeiter",
                password_hash=password_hasher.hash("mitarbeiter-passwort-2026"),
                roles=[role],
            )
        )
        db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "mitarbeiter", "password": "mitarbeiter-passwort-2026"},
    )
    assert response.status_code == 200
    assert client.get("/api/v1/customers").status_code == 403


def test_management_cannot_grant_or_change_administrator_role(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "geschaeftsfuehrung",
            "password": "management-test-passwort-2026",
        },
    )
    assert login.status_code == 200
    csrf = login.cookies.get("securityops_csrf", "")
    headers = {"X-CSRF-Token": csrf}

    elevated_user = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "solladminwerden",
            "email": "newadmin@example.com",
            "full_name": "Unberechtigter Administrator",
            "password": "langes-testpasswort-2026",
            "role_codes": ["administrator"],
        },
    )
    assert elevated_user.status_code == 403

    with TestingSessionLocal() as db:
        admin_id = str(db.query(User).filter_by(username="admin").one().id)
    assert (
        client.patch(
            f"/api/v1/users/{admin_id}",
            headers=headers,
            json={"role_codes": ["employee"]},
        ).status_code
        == 403
    )


def test_login_rate_limit(client: TestClient) -> None:
    responses = [
        client.post(
            "/api/v1/auth/login",
            json={"username": "unknown", "password": "nicht-das-passwort"},
        )
        for _ in range(6)
    ]
    assert all(response.status_code == 401 for response in responses[:5])
    assert responses[5].status_code == 429


def test_password_change_revokes_sessions(client: TestClient) -> None:
    csrf = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    ).cookies.get("securityops_csrf", "")
    response = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": csrf},
        json={
            "current_password": ADMIN_PASSWORD,
            "new_password": "neues-sehr-sicheres-passwort-2026",
        },
    )
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": ADMIN_PASSWORD},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "neues-sehr-sicheres-passwort-2026"},
        ).status_code
        == 200
    )
