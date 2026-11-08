from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import AuthPrincipal, add_audit_entry, require_permission
from app.database import get_db
from app.models import (
    Customer,
    ObjectContact,
    ObjectHistory,
    ObjectSensitiveData,
    ObjectUserAssignment,
    SecurityObject,
    User,
)
from app.object_schemas import (
    ObjectAssignableUserRead,
    ObjectAssignmentCreate,
    ObjectAssignmentRead,
    ObjectContactCreate,
    ObjectContactRead,
    ObjectContactUpdate,
    ObjectCreate,
    ObjectHistoryRead,
    ObjectPage,
    ObjectRead,
    ObjectSensitiveDataInput,
    ObjectSensitiveDataRead,
    ObjectUpdate,
)
from app.object_security import ObjectDataEncryptionError, decrypt_object_data, encrypt_object_data

router = APIRouter()


def object_query():
    return select(SecurityObject).options(
        selectinload(SecurityObject.customer),
        selectinload(SecurityObject.object_manager),
        selectinload(SecurityObject.contacts),
    )


def get_object_or_404(db: Session, object_id: UUID) -> SecurityObject:
    site = db.scalar(object_query().where(SecurityObject.id == object_id))
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objekt nicht gefunden")
    return site


def ensure_object_access(
    db: Session,
    site: SecurityObject,
    principal: AuthPrincipal,
) -> None:
    if "objects.read_all" in principal.permission_codes:
        return
    has_assignment = db.scalar(
        select(ObjectUserAssignment.object_id).where(
            ObjectUserAssignment.object_id == site.id,
            ObjectUserAssignment.user_id == principal.user.id,
        )
    )
    if has_assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objekt nicht gefunden")


def ensure_object_manage(
    db: Session,
    site: SecurityObject,
    principal: AuthPrincipal,
) -> None:
    if "objects.manage_all" in principal.permission_codes:
        return
    if "objects.manage" not in principal.permission_codes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Aktion",
        )
    has_assignment = db.scalar(
        select(ObjectUserAssignment.object_id).where(
            ObjectUserAssignment.object_id == site.id,
            ObjectUserAssignment.user_id == principal.user.id,
        )
    )
    if has_assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objekt nicht gefunden")


def ensure_object_not_archived(site: SecurityObject) -> None:
    if site.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archivierte Objekte können nicht geändert werden.",
        )


def record_object_event(
    db: Session,
    *,
    site: SecurityObject,
    actor_id: UUID,
    action: str,
    changed_fields: set[str],
    ip_address: str | None,
) -> None:
    fields = sorted(changed_fields)
    db.add(
        ObjectHistory(
            object_id=site.id,
            actor_id=actor_id,
            action=action,
            changed_fields=fields,
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"objects.{action}",
        entity_type="object",
        entity_id=str(site.id),
        ip_address=ip_address,
        details={"fields": fields},
    )


def ensure_customer_is_available(db: Session, customer_id: UUID) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Kunde nicht gefunden"
        )
    if customer.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Objekte können keinem archivierten Kunden zugeordnet werden.",
        )
    return customer


def ensure_active_user(db: Session, user_id: UUID) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Benutzer nicht gefunden oder deaktiviert.",
        )
    return user


def object_response(site: SecurityObject) -> ObjectRead:
    return ObjectRead.model_validate(site)


@router.get("/objects", response_model=ObjectPage)
def list_objects(
    q: str | None = Query(default=None, max_length=200),
    customer_id: UUID | None = None,
    object_status: Literal["active", "inactive"] | None = Query(default=None, alias="status"),
    include_archived: bool = False,
    sort_by: Literal["name", "object_number", "city", "status", "created_at"] = "name",
    sort_order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.read")),
) -> ObjectPage:
    query = object_query()
    filters = []
    if "objects.read_all" not in principal.permission_codes:
        filters.append(
            SecurityObject.id.in_(
                select(ObjectUserAssignment.object_id).where(
                    ObjectUserAssignment.user_id == principal.user.id
                )
            )
        )
    if not include_archived:
        filters.append(SecurityObject.archived_at.is_(None))
    elif "objects.archive" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für archivierte Objekte")
    if customer_id is not None:
        filters.append(SecurityObject.customer_id == customer_id)
    if object_status:
        filters.append(SecurityObject.status == object_status)
    if q and q.strip():
        term = f"%{q.strip()}%"
        filters.append(
            or_(
                SecurityObject.name.ilike(term),
                SecurityObject.object_number.ilike(term),
                SecurityObject.street.ilike(term),
                SecurityObject.house_number.ilike(term),
                SecurityObject.city.ilike(term),
                SecurityObject.postal_code.ilike(term),
                SecurityObject.customer.has(Customer.company_name.ilike(term)),
            )
        )
    query = query.where(*filters)
    count_query = select(func.count()).select_from(SecurityObject).where(*filters)
    sort_columns = {
        "name": SecurityObject.name,
        "object_number": SecurityObject.object_number,
        "city": SecurityObject.city,
        "status": SecurityObject.status,
        "created_at": SecurityObject.created_at,
    }
    sort_column = sort_columns[sort_by]
    sort_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    items = db.scalars(
        query.order_by(sort_expression, SecurityObject.object_number).limit(limit).offset(offset)
    ).all()
    return ObjectPage(
        items=[object_response(site) for site in items],
        total=db.scalar(count_query) or 0,
        limit=limit,
        offset=offset,
    )


@router.post("/objects", response_model=ObjectRead, status_code=status.HTTP_201_CREATED)
def create_object(
    request: Request,
    payload: ObjectCreate,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.create")),
) -> ObjectRead:
    ensure_customer_is_available(db, payload.customer_id)
    manager = None
    if payload.object_manager_user_id is not None:
        if "objects.assign" not in principal.permission_codes:
            raise HTTPException(
                status_code=403, detail="Keine Berechtigung für Benutzerzuweisungen"
            )
        manager = ensure_active_user(db, payload.object_manager_user_id)

    values = payload.model_dump(exclude={"customer_id", "object_manager_user_id"}, mode="json")
    email = values.pop("email")
    site = SecurityObject(
        customer_id=payload.customer_id,
        object_number=f"O-{uuid4().hex.upper()}",
        object_manager=manager,
        operating_hours=values.pop("operating_hours"),
        qualification_requirements=values.pop("qualification_requirements"),
        email=email.lower() if email else None,
        **values,
    )
    db.add(site)
    db.flush()
    assignment_user_ids = {principal.user.id}
    if manager is not None:
        assignment_user_ids.add(manager.id)
    for user_id in assignment_user_ids:
        db.add(
            ObjectUserAssignment(
                object_id=site.id,
                user_id=user_id,
                assigned_by=principal.user.id,
            )
        )
    record_object_event(
        db,
        site=site,
        actor_id=principal.user.id,
        action="created",
        changed_fields=set(payload.model_fields_set) | {"object_number"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return object_response(get_object_or_404(db, site.id))


@router.get("/objects/assignment-candidates", response_model=list[ObjectAssignableUserRead])
def list_assignment_candidates(
    db: Session = Depends(get_db),
    _principal: AuthPrincipal = Depends(require_permission("objects.assign")),
) -> list[ObjectAssignableUserRead]:
    users = db.scalars(
        select(User).where(User.is_active.is_(True)).order_by(User.full_name, User.username)
    ).all()
    return [
        ObjectAssignableUserRead(id=user.id, username=user.username, full_name=user.full_name)
        for user in users
    ]


@router.get("/objects/{object_id}", response_model=ObjectRead)
def get_object(
    object_id: UUID,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.read")),
) -> ObjectRead:
    site = get_object_or_404(db, object_id)
    ensure_object_access(db, site, principal)
    return object_response(site)


@router.patch("/objects/{object_id}", response_model=ObjectRead)
def update_object(
    request: Request,
    object_id: UUID,
    payload: ObjectUpdate,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.manage")),
) -> ObjectRead:
    site = get_object_or_404(db, object_id)
    ensure_object_manage(db, site, principal)
    ensure_object_not_archived(site)
    changes = payload.model_dump(exclude_unset=True, mode="json")
    manager_id = (
        payload.object_manager_user_id
        if "object_manager_user_id" in payload.model_fields_set
        else ...
    )
    manager_changed = False
    if manager_id is not ... and manager_id is not None:
        if "objects.assign" not in principal.permission_codes:
            raise HTTPException(
                status_code=403, detail="Keine Berechtigung für Benutzerzuweisungen"
            )
        manager = ensure_active_user(db, manager_id)
        if manager.id != site.object_manager_user_id:
            manager_changed = True
            if "objects.assign" not in principal.permission_codes:
                raise HTTPException(
                    status_code=403, detail="Keine Berechtigung für Benutzerzuweisungen"
                )
            if db.get(ObjectUserAssignment, (site.id, manager.id)) is None:
                db.add(
                    ObjectUserAssignment(
                        object_id=site.id,
                        user_id=manager.id,
                        assigned_by=principal.user.id,
                    )
                )
        site.object_manager = manager
        changes.pop("object_manager_user_id", None)
    elif manager_id is None:
        manager_changed = site.object_manager_user_id is not None
        site.object_manager = None
        changes.pop("object_manager_user_id", None)

    customer_id = UUID(changes.pop("customer_id")) if "customer_id" in changes else None
    changed_fields = set()
    if customer_id is not None:
        ensure_customer_is_available(db, customer_id)
        if site.customer_id != customer_id:
            site.customer_id = customer_id
            changed_fields.add("customer_id")
    for field, value in changes.items():
        if field == "email" and value is not None:
            value = str(value).lower()
        if isinstance(value, str):
            value = value.strip() or None
        if getattr(site, field) != value:
            setattr(site, field, value)
            changed_fields.add(field)
    if manager_changed:
        changed_fields.add("object_manager_user_id")
    if changed_fields:
        record_object_event(
            db,
            site=site,
            actor_id=principal.user.id,
            action="updated",
            changed_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
        )
    db.commit()
    return object_response(get_object_or_404(db, site.id))


@router.post("/objects/{object_id}/archive", response_model=ObjectRead)
def archive_object(
    request: Request,
    object_id: UUID,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.archive")),
) -> ObjectRead:
    site = get_object_or_404(db, object_id)
    ensure_object_access(db, site, principal)
    if site.archived_at is not None:
        raise HTTPException(status_code=409, detail="Objekt ist bereits archiviert.")
    site.archived_at = datetime.now(UTC)
    record_object_event(
        db,
        site=site,
        actor_id=principal.user.id,
        action="archived",
        changed_fields={"archived_at"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return object_response(get_object_or_404(db, site.id))


@router.get("/objects/{object_id}/history", response_model=list[ObjectHistoryRead])
def list_object_history(
    object_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.read")),
) -> list[ObjectHistoryRead]:
    site = get_object_or_404(db, object_id)
    ensure_object_access(db, site, principal)
    rows = db.scalars(
        select(ObjectHistory)
        .where(ObjectHistory.object_id == object_id)
        .order_by(ObjectHistory.created_at.desc(), ObjectHistory.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return [ObjectHistoryRead.model_validate(row) for row in rows]


@router.get("/objects/{object_id}/contacts", response_model=list[ObjectContactRead])
def list_object_contacts(
    object_id: UUID,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.read")),
) -> list[ObjectContactRead]:
    site = get_object_or_404(db, object_id)
    ensure_object_access(db, site, principal)
    return [ObjectContactRead.model_validate(contact) for contact in site.contacts]


@router.post(
    "/objects/{object_id}/contacts",
    response_model=ObjectContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_object_contact(
    request: Request,
    object_id: UUID,
    payload: ObjectContactCreate,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.manage")),
) -> ObjectContactRead:
    site = get_object_or_404(db, object_id)
    ensure_object_manage(db, site, principal)
    ensure_object_not_archived(site)
    if payload.is_primary:
        for contact in site.contacts:
            contact.is_primary = False
        db.flush()
    contact = ObjectContact(
        object_id=site.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        responsibility=payload.responsibility.strip() if payload.responsibility else None,
        email=str(payload.email).lower() if payload.email else None,
        phone=payload.phone.strip() if payload.phone else None,
        is_primary=payload.is_primary,
    )
    db.add(contact)
    db.flush()
    record_object_event(
        db,
        site=site,
        actor_id=principal.user.id,
        action="contact_created",
        changed_fields={"contacts"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return ObjectContactRead.model_validate(contact)


@router.patch(
    "/objects/{object_id}/contacts/{contact_id}",
    response_model=ObjectContactRead,
)
def update_object_contact(
    request: Request,
    object_id: UUID,
    contact_id: UUID,
    payload: ObjectContactUpdate,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.manage")),
) -> ObjectContactRead:
    site = get_object_or_404(db, object_id)
    ensure_object_manage(db, site, principal)
    ensure_object_not_archived(site)
    contact = next((item for item in site.contacts if item.id == contact_id), None)
    if contact is None:
        raise HTTPException(status_code=404, detail="Objektkontakt nicht gefunden")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_primary") is True:
        for existing in site.contacts:
            existing.is_primary = False
        db.flush()
    changed_fields = set()
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip() or None
        if field == "email" and value is not None:
            value = str(value).lower()
        if getattr(contact, field) != value:
            setattr(contact, field, value)
            changed_fields.add("contacts")
    if changed_fields:
        record_object_event(
            db,
            site=site,
            actor_id=principal.user.id,
            action="contact_updated",
            changed_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
        )
    db.commit()
    return ObjectContactRead.model_validate(contact)


@router.delete("/objects/{object_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_object_contact(
    request: Request,
    object_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.manage")),
) -> None:
    site = get_object_or_404(db, object_id)
    ensure_object_manage(db, site, principal)
    ensure_object_not_archived(site)
    contact = next((item for item in site.contacts if item.id == contact_id), None)
    if contact is None:
        raise HTTPException(status_code=404, detail="Objektkontakt nicht gefunden")
    site.contacts.remove(contact)
    db.delete(contact)
    record_object_event(
        db,
        site=site,
        actor_id=principal.user.id,
        action="contact_deleted",
        changed_fields={"contacts"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()


@router.get(
    "/objects/{object_id}/assignments",
    response_model=list[ObjectAssignmentRead],
)
def list_object_assignments(
    object_id: UUID,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.assign")),
) -> list[ObjectAssignmentRead]:
    site = get_object_or_404(db, object_id)
    ensure_object_access(db, site, principal)
    assignments = db.scalars(
        select(ObjectUserAssignment)
        .options(selectinload(ObjectUserAssignment.user))
        .where(ObjectUserAssignment.object_id == object_id)
        .order_by(ObjectUserAssignment.assigned_at, ObjectUserAssignment.user_id)
    ).all()
    return [
        ObjectAssignmentRead(
            user_id=item.user_id,
            username=item.user.username,
            full_name=item.user.full_name,
            assigned_at=item.assigned_at,
        )
        for item in assignments
    ]


@router.post(
    "/objects/{object_id}/assignments",
    response_model=ObjectAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_user_to_object(
    request: Request,
    object_id: UUID,
    payload: ObjectAssignmentCreate,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.assign")),
) -> ObjectAssignmentRead:
    site = get_object_or_404(db, object_id)
    ensure_object_manage(db, site, principal)
    ensure_object_not_archived(site)
    user = ensure_active_user(db, payload.user_id)
    existing = db.get(ObjectUserAssignment, (site.id, user.id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Benutzer ist dem Objekt bereits zugewiesen.")
    assignment = ObjectUserAssignment(
        object_id=site.id,
        user_id=user.id,
        assigned_by=principal.user.id,
    )
    db.add(assignment)
    record_object_event(
        db,
        site=site,
        actor_id=principal.user.id,
        action="user_assigned",
        changed_fields={"assignments"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return ObjectAssignmentRead(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        assigned_at=assignment.assigned_at,
    )


@router.delete(
    "/objects/{object_id}/assignments/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user_from_object(
    request: Request,
    object_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.assign")),
) -> None:
    site = get_object_or_404(db, object_id)
    ensure_object_manage(db, site, principal)
    ensure_object_not_archived(site)
    if site.object_manager_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Die Objektleitung muss vor dem Entfernen neu zugewiesen werden.",
        )
    assignment = db.get(ObjectUserAssignment, (site.id, user_id))
    if assignment is None:
        raise HTTPException(status_code=404, detail="Objektzuweisung nicht gefunden")
    db.delete(assignment)
    record_object_event(
        db,
        site=site,
        actor_id=principal.user.id,
        action="user_unassigned",
        changed_fields={"assignments"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()


@router.get(
    "/objects/{object_id}/sensitive-data",
    response_model=ObjectSensitiveDataRead,
)
def get_object_sensitive_data(
    object_id: UUID,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.sensitive.read")),
) -> ObjectSensitiveDataRead:
    site = get_object_or_404(db, object_id)
    ensure_object_access(db, site, principal)
    record = db.get(ObjectSensitiveData, object_id)
    if record is None:
        payload = ObjectSensitiveDataInput().model_dump()
        updated_at = None
    else:
        try:
            payload = decrypt_object_data(object_id, record.ciphertext)
        except ObjectDataEncryptionError as exc:
            raise HTTPException(
                status_code=500,
                detail="Sensible Objektdaten können nicht sicher entschlüsselt werden.",
            ) from exc
        updated_at = record.updated_at
    return ObjectSensitiveDataRead(**payload, updated_at=updated_at)


@router.put(
    "/objects/{object_id}/sensitive-data",
    response_model=ObjectSensitiveDataRead,
)
def update_object_sensitive_data(
    request: Request,
    object_id: UUID,
    payload: ObjectSensitiveDataInput,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("objects.sensitive.write")),
) -> ObjectSensitiveDataRead:
    site = get_object_or_404(db, object_id)
    ensure_object_access(db, site, principal)
    ensure_object_not_archived(site)
    next_payload = payload.model_dump()
    record = db.get(ObjectSensitiveData, object_id)
    previous_payload = ObjectSensitiveDataInput().model_dump()
    if record is not None:
        try:
            previous_payload = decrypt_object_data(object_id, record.ciphertext)
        except ObjectDataEncryptionError as exc:
            raise HTTPException(
                status_code=500,
                detail="Sensible Objektdaten können nicht sicher entschlüsselt werden.",
            ) from exc
    changed_fields = {
        field for field, value in next_payload.items() if previous_payload.get(field) != value
    }
    ciphertext = encrypt_object_data(object_id, next_payload)
    now = datetime.now(UTC)
    if record is None:
        record = ObjectSensitiveData(
            object_id=object_id,
            ciphertext=ciphertext,
            updated_by=principal.user.id,
            updated_at=now,
        )
        db.add(record)
    elif changed_fields:
        record.ciphertext = ciphertext
        record.updated_by = principal.user.id
        record.updated_at = now
    if changed_fields:
        record_object_event(
            db,
            site=site,
            actor_id=principal.user.id,
            action="sensitive_data_updated",
            changed_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
        )
    db.commit()
    return ObjectSensitiveDataRead(**next_payload, updated_at=record.updated_at)
