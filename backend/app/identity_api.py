from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import (
    AuthPrincipal,
    add_audit_entry,
    clear_session_cookies,
    get_auth_principal,
    hash_token,
    issue_session_tokens,
    require_permission,
    set_session_cookies,
)
from app.config import get_settings
from app.database import get_db
from app.models import AuditLog, Role, User, UserSession, user_roles
from app.rate_limit import limiter
from app.schemas import (
    AuditLogRead,
    LoginRequest,
    PasswordChange,
    RoleRead,
    SessionRead,
    UserCreate,
    UserRead,
    UserUpdate,
)

password_hasher = PasswordHash.recommended()
dummy_password_hash = password_hasher.hash("SecurityOps-invalid-account-password")
router = APIRouter()


def user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=sorted(role.code for role in user.roles),
        permissions=sorted(
            {permission.code for role in user.roles for permission in role.permissions}
        ),
    )


@router.post("/auth/login", response_model=SessionRead)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> SessionRead:
    username = payload.username.strip().lower()
    user = db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.username == username)
    )
    stored_hash = user.password_hash if user else dummy_password_hash
    valid_password = password_hasher.verify(payload.password, stored_hash)
    if user is None or not user.is_active or not valid_password:
        add_audit_entry(
            db,
            actor_id=user.id if user else None,
            action="auth.login_failed",
            entity_type="user",
            entity_id=str(user.id) if user else None,
            ip_address=request.client.host if request.client else None,
            details={"username": username},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzername oder Passwort ist ungültig",
        )

    settings = get_settings()
    now = datetime.now(UTC)
    session_token, csrf_token = issue_session_tokens()
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_token(session_token),
        csrf_token_hash=hash_token(csrf_token),
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=settings.session_idle_minutes),
        absolute_expires_at=now + timedelta(hours=settings.session_absolute_hours),
    )
    db.add(user_session)
    add_audit_entry(
        db,
        actor_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    set_session_cookies(response, session_token, csrf_token)
    return SessionRead(user=user_read(user))


@router.get("/auth/me", response_model=SessionRead)
def get_me(
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> SessionRead:
    return SessionRead(user=user_read(principal.user))


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="auth.logout",
        entity_type="user",
        entity_id=str(principal.user.id),
        ip_address=request.client.host if request.client else None,
    )
    db.delete(principal.session)
    db.commit()
    clear_session_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/auth/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    request: Request,
    response: Response,
    payload: PasswordChange,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    if not password_hasher.verify(payload.current_password, principal.user.password_hash):
        raise HTTPException(status_code=400, detail="Das aktuelle Passwort ist nicht korrekt")
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=422, detail="Das neue Passwort muss sich vom bisherigen unterscheiden"
        )

    principal.user.password_hash = password_hasher.hash(payload.new_password)
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="auth.password_changed",
        entity_type="user",
        entity_id=str(principal.user.id),
        ip_address=request.client.host if request.client else None,
    )
    db.query(UserSession).filter(UserSession.user_id == principal.user.id).delete(
        synchronize_session=False
    )
    db.commit()
    clear_session_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/roles", response_model=list[RoleRead])
def list_roles(
    _principal: Annotated[AuthPrincipal, Depends(require_permission("roles.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[RoleRead]:
    roles = db.scalars(
        select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
    ).all()
    return [
        RoleRead(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            permissions=sorted(permission.code for permission in role.permissions),
        )
        for role in roles
    ]


@router.get("/users", response_model=list[UserRead])
def list_users(
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserRead]:
    if "users.read" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion")
    users = db.scalars(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .order_by(User.username)
    ).all()
    return [user_read(user) for user in users]


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    payload: UserCreate,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    if "users.manage" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion")
    normalized_codes = [code.strip().lower() for code in payload.role_codes]
    roles = db.scalars(select(Role).where(Role.code.in_(normalized_codes))).all()
    if len(roles) != len(normalized_codes):
        raise HTTPException(status_code=422, detail="Mindestens eine Rolle ist unbekannt")
    if (
        any(role.code == "administrator" for role in roles)
        and "users.manage_admin" not in principal.permission_codes
    ):
        raise HTTPException(
            status_code=403,
            detail="Nur Administratoren dürfen Administratorrechte vergeben",
        )

    user = User(
        username=payload.username.strip().lower(),
        email=str(payload.email).lower(),
        full_name=payload.full_name.strip(),
        password_hash=password_hasher.hash(payload.password),
        roles=roles,
    )
    db.add(user)
    try:
        db.flush()
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="users.created",
            entity_type="user",
            entity_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            details={"roles": normalized_codes},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Benutzername oder E-Mail-Adresse ist bereits vergeben",
        ) from exc

    created = db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user.id)
    )
    return user_read(created)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    request: Request,
    user_id: UUID,
    payload: UserUpdate,
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    if "users.manage" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion")
    if user_id == principal.user.id:
        raise HTTPException(
            status_code=409,
            detail="Das eigene Administratorkonto kann hier nicht geändert werden",
        )

    user = db.scalar(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    changes = payload.model_dump(exclude_unset=True)
    new_roles = user.roles
    if "role_codes" in changes:
        role_codes = [code.strip().lower() for code in changes["role_codes"]]
        new_roles = db.scalars(select(Role).where(Role.code.in_(role_codes))).all()
        if len(new_roles) != len(role_codes):
            raise HTTPException(status_code=422, detail="Mindestens eine Rolle ist unbekannt")

    current_admin = any(role.code == "administrator" for role in user.roles)
    desired_admin = any(role.code == "administrator" for role in new_roles)
    if (current_admin or desired_admin) and "users.manage_admin" not in principal.permission_codes:
        raise HTTPException(
            status_code=403,
            detail="Nur Administratoren dürfen Administratorrechte ändern",
        )

    was_active_admin = user.is_active and current_admin
    will_be_active = changes.get("is_active", user.is_active)
    will_be_admin = any(role.code == "administrator" for role in new_roles)
    if was_active_admin and (not will_be_active or not will_be_admin):
        db.scalar(select(Role).where(Role.code == "administrator").with_for_update())
        admin_count = (
            db.scalar(
                select(func.count(User.id))
                .join(user_roles, user_roles.c.user_id == User.id)
                .join(Role, Role.id == user_roles.c.role_id)
                .where(User.is_active.is_(True), Role.code == "administrator")
            )
            or 0
        )
        if admin_count <= 1:
            raise HTTPException(
                status_code=409,
                detail="Der letzte aktive Administrator kann nicht deaktiviert oder herabgestuft werden",
            )

    if "is_active" in changes:
        if changes["is_active"] is None:
            raise HTTPException(status_code=422, detail="is_active darf nicht null sein")
        user.is_active = changes["is_active"]
    if "role_codes" in changes:
        user.roles = new_roles

    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="users.updated",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        details={
            "active": user.is_active,
            "roles": sorted(role.code for role in user.roles),
        },
    )
    if not user.is_active:
        db.query(UserSession).filter(UserSession.user_id == user.id).delete(
            synchronize_session=False
        )
    db.commit()
    refreshed = db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user.id)
    )
    return user_read(refreshed)


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> list[AuditLogRead]:
    if "audit.read" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion")
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="Limit muss zwischen 1 und 100 liegen")
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [AuditLogRead.model_validate(row) for row in rows]
