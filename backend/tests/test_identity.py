from uuid import UUID

from conftest import ADMIN_PASSWORD, TestingSessionLocal
from fastapi.testclient import TestClient

from app.identity_api import password_hasher
from app.mfa import totp_code, totp_counter_at
from app.models import Role, User, UserMFARecoveryCode, UserSession
from app.rate_limit import limiter


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
    elevated_role = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "hr-konto",
            "email": "hr-konto@example.com",
            "full_name": "HR Konto",
            "password": "langes-testpasswort-2026",
            "role_codes": ["hr"],
        },
    )
    assert elevated_role.status_code == 403


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


def test_global_rate_limit_applies_to_undecorated_routes(client: TestClient) -> None:
    responses = [client.get("/health/live") for _ in range(121)]
    assert all(response.status_code == 200 for response in responses[:120])
    assert responses[120].status_code == 429
    assert responses[120].json()["detail"] == "Zu viele Anfragen. Bitte später erneut versuchen."


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


def test_mfa_enrollment_totp_replay_and_single_use_recovery_codes(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    csrf = login.cookies.get("securityops_csrf", "")
    headers = {"X-CSRF-Token": csrf}

    setup = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers,
        json={"current_password": "falsches-passwort"},
    )
    assert setup.status_code == 400
    setup = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers,
        json={"current_password": ADMIN_PASSWORD},
    )
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    assert setup.json()["otpauth_uri"].startswith("otpauth://totp/")
    with TestingSessionLocal() as db:
        admin = db.query(User).filter_by(username="admin").one()
        assert admin.mfa_secret_encrypted != secret
        assert admin.mfa_enabled is False

    enable_code = totp_code(secret, totp_counter_at())
    enabled = client.post(
        "/api/v1/auth/mfa/enable",
        headers=headers,
        json={"code": enable_code},
    )
    assert enabled.status_code == 200
    recovery_codes = enabled.json()["recovery_codes"]
    assert len(recovery_codes) == 10
    assert all(len(code) == 32 for code in recovery_codes)
    assert len(set(recovery_codes)) == 10
    assert (
        client.post(
            "/api/v1/auth/mfa/enable",
            headers=headers,
            json={"code": enable_code},
        ).status_code
        == 409
    )
    with TestingSessionLocal() as db:
        assert db.query(UserMFARecoveryCode).count() == 10

    next_code = totp_code(secret, totp_counter_at() + 1)
    mfa_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": ADMIN_PASSWORD,
            "mfa_code": next_code,
        },
    )
    assert mfa_login.status_code == 200
    assert "secret" not in mfa_login.text
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": ADMIN_PASSWORD,
                "mfa_code": next_code,
            },
        ).status_code
        == 401
    )

    recovery_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": ADMIN_PASSWORD,
            "recovery_code": recovery_codes[0],
        },
    )
    assert recovery_login.status_code == 200
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": ADMIN_PASSWORD,
                "recovery_code": recovery_codes[0],
            },
        ).status_code
        == 401
    )
    with TestingSessionLocal() as db:
        assert db.query(UserMFARecoveryCode).count() == 9


def test_session_overview_and_foreign_session_revocation_require_permission(
    client: TestClient,
) -> None:
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    admin_csrf = admin_login.cookies.get("securityops_csrf", "")
    created = client.post(
        "/api/v1/users",
        headers={"X-CSRF-Token": admin_csrf},
        json={
            "username": "session-user",
            "email": "session-user@example.com",
            "full_name": "Session User",
            "password": "langes-testpasswort-2026",
            "role_codes": ["employee"],
        },
    )
    assert created.status_code == 201
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "session-user", "password": "langes-testpasswort-2026"},
            headers={"User-Agent": "Testbrowser/1.0"},
        ).status_code
        == 200
    )
    with TestingSessionLocal() as db:
        foreign_session = db.query(UserSession).filter_by(user_id=UUID(created.json()["id"])).one()
        foreign_session_id = str(foreign_session.id)
        assert foreign_session.ip_address
        assert foreign_session.user_agent == "Testbrowser/1.0"

    management_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "geschaeftsfuehrung",
            "password": "management-test-passwort-2026",
        },
    )
    management_csrf = management_login.cookies.get("securityops_csrf", "")
    own_sessions = client.get("/api/v1/auth/sessions")
    assert own_sessions.status_code == 200
    assert len(own_sessions.json()) == 1
    assert own_sessions.json()[0]["is_current"] is True
    assert "token" not in own_sessions.text
    assert client.get(f"/api/v1/users/{created.json()['id']}/sessions").status_code == 403
    assert (
        client.delete(
            f"/api/v1/auth/sessions/{foreign_session_id}",
            headers={"X-CSRF-Token": management_csrf},
        ).status_code
        == 403
    )

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    admin_csrf = admin_login.cookies.get("securityops_csrf", "")
    listed = client.get(f"/api/v1/users/{created.json()['id']}/sessions")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["is_current"] is False
    revoked = client.delete(
        f"/api/v1/auth/sessions/{foreign_session_id}",
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert revoked.status_code == 204
    assert (
        client.delete(
            f"/api/v1/auth/sessions/{foreign_session_id}",
            headers={"X-CSRF-Token": admin_csrf},
        ).status_code
        == 404
    )


def test_admin_password_reset_requires_permission_and_forces_change(client: TestClient) -> None:
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    admin_csrf = admin_login.cookies.get("securityops_csrf", "")
    created = client.post(
        "/api/v1/users",
        headers={"X-CSRF-Token": admin_csrf},
        json={
            "username": "reset-user",
            "email": "reset-user@example.com",
            "full_name": "Reset User",
            "password": "langes-testpasswort-2026",
            "role_codes": ["employee"],
        },
    )
    assert created.status_code == 201

    management_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "geschaeftsfuehrung",
            "password": "management-test-passwort-2026",
        },
    )
    management_csrf = management_login.cookies.get("securityops_csrf", "")
    assert (
        client.post(
            f"/api/v1/users/{created.json()['id']}/reset-password",
            headers={"X-CSRF-Token": management_csrf},
            json={"temporary_password": "voruebergehend-sehr-sicher"},
        ).status_code
        == 403
    )

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    admin_csrf = admin_login.cookies.get("securityops_csrf", "")
    temporary_password = "voruebergehend-sehr-sicher"
    reset = client.post(
        f"/api/v1/users/{created.json()['id']}/reset-password",
        headers={"X-CSRF-Token": admin_csrf},
        json={"temporary_password": temporary_password},
    )
    assert reset.status_code == 204
    assert not reset.content
    limiter.reset()
    forced_login = client.post(
        "/api/v1/auth/login",
        json={"username": "reset-user", "password": temporary_password},
    )
    assert forced_login.status_code == 200
    assert forced_login.json()["password_change_required"] is True
    assert client.get("/api/v1/auth/me").status_code == 403
    csrf = forced_login.cookies.get("securityops_csrf", "")
    changed = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": csrf},
        json={
            "current_password": temporary_password,
            "new_password": "neues-benutzer-passwort-2026",
        },
    )
    assert changed.status_code == 204
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "reset-user", "password": temporary_password},
        ).status_code
        == 401
    )
    updated_login = client.post(
        "/api/v1/auth/login",
        json={"username": "reset-user", "password": "neues-benutzer-passwort-2026"},
    )
    assert updated_login.status_code == 200
    assert updated_login.json()["password_change_required"] is False
