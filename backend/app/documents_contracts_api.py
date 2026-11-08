from datetime import UTC, date, datetime
from pathlib import PurePosixPath
from typing import Annotated
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, add_audit_entry, require_permission
from app.config import get_settings
from app.database import get_db
from app.document_storage import read_file, remove_file, sha256_hex, store_file, validate_upload
from app.documents_contracts_schemas import (
    ApprovalDecision,
    ContractCreate,
    ContractHistoryRead,
    ContractPage,
    ContractRead,
    ContractUpdate,
    DocumentApprovalQueueItem,
    DocumentApprovalRead,
    DocumentCreate,
    DocumentDetailRead,
    DocumentHistoryRead,
    DocumentPage,
    DocumentRead,
    DocumentReadReceiptRead,
    DocumentUpdate,
    DocumentVersionRead,
    ReminderRead,
    ReminderSettingsRead,
    ReminderSettingsUpdate,
    ReminderStatusUpdate,
)
from app.models import (
    Contract,
    ContractHistory,
    Customer,
    Document,
    DocumentApproval,
    DocumentContractReminder,
    DocumentContractReminderSettings,
    DocumentHistory,
    DocumentReadReceipt,
    DocumentVersion,
    Employee,
    ObjectAssignment,
    SecurityObject,
)

router = APIRouter()


def _now() -> datetime:
    return datetime.now(UTC)


def _employee_id_for_user(db: Session, user_id: UUID) -> UUID | None:
    return db.scalar(select(Employee.id).where(Employee.user_id == user_id))


def _global_object_access(principal: AuthPrincipal) -> bool:
    return bool(
        {"administrator", "management"} & set(principal.role_codes)
        or {"objects.read_all", "objects.manage_all"} & principal.permission_codes
    )


def _scope_document_query(query, db: Session, principal: AuthPrincipal):
    if not _global_object_access(principal):
        object_ids = select(ObjectAssignment.object_id).where(
            ObjectAssignment.user_id == principal.user.id
        )
        query = query.where(or_(Document.object_id.is_(None), Document.object_id.in_(object_ids)))

    employee_id = _employee_id_for_user(db, principal.user.id)
    if "employees.sensitive.read" not in principal.permission_codes:
        query = query.where(
            or_(Document.employee_id.is_(None), Document.employee_id == employee_id)
        )
    if "customers.read" not in principal.permission_codes:
        query = query.where(
            or_(
                Document.customer_id.is_(None),
                Document.object_id.is_not(None),
                Document.employee_id == employee_id,
            )
        )
    if "documents.update" not in principal.permission_codes:
        query = query.where(
            or_(
                Document.customer_id.is_not(None),
                Document.object_id.is_not(None),
                Document.employee_id.is_not(None),
            )
        )
    return query


def _scope_contract_query(query, db: Session, principal: AuthPrincipal):
    if not _global_object_access(principal):
        object_ids = select(ObjectAssignment.object_id).where(
            ObjectAssignment.user_id == principal.user.id
        )
        query = query.where(or_(Contract.object_id.is_(None), Contract.object_id.in_(object_ids)))

    employee_id = _employee_id_for_user(db, principal.user.id)
    if "employees.sensitive.read" not in principal.permission_codes:
        query = query.where(
            or_(Contract.employee_id.is_(None), Contract.employee_id == employee_id)
        )
    if "customers.read" not in principal.permission_codes:
        query = query.where(
            or_(
                Contract.object_id.is_not(None),
                Contract.employee_id == employee_id,
            )
        )
    return query


def _ensure_document_scope(db: Session, document: Document, principal: AuthPrincipal) -> None:
    if document.object_id is not None and not _global_object_access(principal):
        assigned = db.scalar(
            select(ObjectAssignment.id).where(
                ObjectAssignment.object_id == document.object_id,
                ObjectAssignment.user_id == principal.user.id,
            )
        )
        if assigned is None:
            raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    employee_id = _employee_id_for_user(db, principal.user.id)
    if (
        document.employee_id is not None
        and "employees.sensitive.read" not in principal.permission_codes
        and document.employee_id != employee_id
    ):
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    if (
        document.customer_id is not None
        and document.object_id is None
        and document.employee_id is None
        and "customers.read" not in principal.permission_codes
    ):
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    if (
        document.customer_id is None
        and document.object_id is None
        and document.employee_id is None
        and "documents.update" not in principal.permission_codes
    ):
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")


def _ensure_contract_scope(db: Session, contract: Contract, principal: AuthPrincipal) -> None:
    if contract.object_id is not None and not _global_object_access(principal):
        assigned = db.scalar(
            select(ObjectAssignment.id).where(
                ObjectAssignment.object_id == contract.object_id,
                ObjectAssignment.user_id == principal.user.id,
            )
        )
        if assigned is None:
            raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    employee_id = _employee_id_for_user(db, principal.user.id)
    if (
        contract.employee_id is not None
        and "employees.sensitive.read" not in principal.permission_codes
        and contract.employee_id != employee_id
    ):
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    if (
        contract.object_id is None
        and contract.employee_id is None
        and "customers.read" not in principal.permission_codes
    ):
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")


def _ensure_document_link_scope(
    db: Session,
    principal: AuthPrincipal,
    customer_id: UUID | None,
    object_id: UUID | None,
    employee_id: UUID | None,
) -> None:
    if object_id is not None and not _global_object_access(principal):
        assigned = db.scalar(
            select(ObjectAssignment.id).where(
                ObjectAssignment.object_id == object_id,
                ObjectAssignment.user_id == principal.user.id,
            )
        )
        if assigned is None:
            raise HTTPException(
                status_code=403, detail="Keine Berechtigung für das zugeordnete Objekt."
            )
    if (
        employee_id is not None
        and "employees.sensitive.manage" not in principal.permission_codes
        and employee_id != _employee_id_for_user(db, principal.user.id)
    ):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für die Personalzuordnung.")
    if (
        customer_id is not None
        and object_id is None
        and employee_id is None
        and "customers.read" not in principal.permission_codes
    ):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für die Kundenzuordnung.")


def _ensure_contract_link_scope(
    db: Session,
    principal: AuthPrincipal,
    customer_id: UUID,
    object_id: UUID | None,
    employee_id: UUID | None,
) -> None:
    if object_id is not None and not _global_object_access(principal):
        assigned = db.scalar(
            select(ObjectAssignment.id).where(
                ObjectAssignment.object_id == object_id,
                ObjectAssignment.user_id == principal.user.id,
            )
        )
        if assigned is None:
            raise HTTPException(
                status_code=403, detail="Keine Berechtigung für das zugeordnete Objekt."
            )
    if (
        employee_id is not None
        and "employees.sensitive.manage" not in principal.permission_codes
        and employee_id != _employee_id_for_user(db, principal.user.id)
    ):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für die Personalzuordnung.")
    if (
        object_id is None
        and employee_id is None
        and "customers.read" not in principal.permission_codes
    ):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für die Kundenzuordnung.")


def _get_document(db: Session, document_id: UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    return document


def _get_contract(db: Session, contract_id: UUID) -> Contract:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    return contract


def _get_version(db: Session, version_id: UUID) -> DocumentVersion:
    version = db.get(DocumentVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Dokumentversion nicht gefunden")
    return version


def _document_version_read(db: Session, document_id: UUID) -> DocumentVersionRead | None:
    version = db.scalar(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version.desc())
        .limit(1)
    )
    return DocumentVersionRead.model_validate(version) if version is not None else None


def _document_read(db: Session, document: Document) -> DocumentRead:
    data = {
        "id": document.id,
        "document_number": document.document_number,
        "title": document.title,
        "description": document.description,
        "category": document.category,
        "status": document.status,
        "customer_id": document.customer_id,
        "object_id": document.object_id,
        "employee_id": document.employee_id,
        "expires_on": document.expires_on,
        "archived_at": document.archived_at,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "latest_version": _document_version_read(db, document.id),
    }
    return DocumentRead.model_validate(data)


def _document_history(
    db: Session,
    document: Document,
    actor_id: UUID,
    action: str,
    fields: list[str] | None = None,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        DocumentHistory(
            document_id=document.id,
            actor_id=actor_id,
            action=action,
            changed_fields=fields or [],
            details=details or {},
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"documents.{action}",
        entity_type="document",
        entity_id=str(document.id),
        details=details or {"fields": fields or []},
    )


def _contract_history(
    db: Session,
    contract: Contract,
    actor_id: UUID,
    action: str,
    fields: list[str] | None = None,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        ContractHistory(
            contract_id=contract.id,
            actor_id=actor_id,
            action=action,
            changed_fields=fields or [],
            details=details or {},
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"contracts.{action}",
        entity_type="contract",
        entity_id=str(contract.id),
        details=details or {"fields": fields or []},
    )


def _validate_document_links(
    db: Session, customer_id: UUID | None, object_id: UUID | None, employee_id: UUID | None
) -> UUID | None:
    if object_id is not None:
        object_row = db.get(SecurityObject, object_id)
        if object_row is None or object_row.archived_at is not None:
            raise HTTPException(
                status_code=422, detail="Das zugeordnete Objekt ist nicht verfügbar."
            )
        if customer_id is not None and customer_id != object_row.customer_id:
            raise HTTPException(status_code=422, detail="Objekt und Kunde passen nicht zusammen.")
        customer_id = object_row.customer_id
    if customer_id is not None:
        customer = db.get(Customer, customer_id)
        if customer is None or customer.archived_at is not None:
            raise HTTPException(
                status_code=422, detail="Der zugeordnete Kunde ist nicht verfügbar."
            )
    if employee_id is not None:
        employee = db.get(Employee, employee_id)
        if employee is None or employee.archived_at is not None:
            raise HTTPException(
                status_code=422, detail="Der zugeordnete Mitarbeiter ist nicht verfügbar."
            )
    return customer_id


def _upload_content(file: UploadFile) -> tuple[str, str, bytes]:
    maximum = get_settings().document_max_upload_bytes
    if maximum <= 0:
        raise RuntimeError("DOCUMENT_MAX_UPLOAD_BYTES muss größer als 0 sein.")
    if file.size is not None and file.size > maximum:
        raise HTTPException(
            status_code=413,
            detail=f"Die Datei überschreitet das Limit von {maximum} Bytes.",
        )
    content = file.file.read(maximum + 1)
    safe_name, media_type = validate_upload(file.filename, file.content_type, content)
    return safe_name, media_type, content


def _remove_after_rollback(storage_key: str | None) -> None:
    if storage_key is not None:
        remove_file(storage_key)


@router.get("/documents", response_model=DocumentPage)
def list_documents(
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.read"))],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    customer_id: UUID | None = None,
    object_id: UUID | None = None,
    employee_id: UUID | None = None,
    include_archived: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> DocumentPage:
    query = _scope_document_query(select(Document), db, principal)
    if not include_archived or "documents.archive" not in principal.permission_codes:
        query = query.where(Document.archived_at.is_(None))
    if status_filter:
        query = query.where(Document.status == status_filter)
    if category:
        query = query.where(Document.category == category)
    if customer_id:
        query = query.where(Document.customer_id == customer_id)
    if object_id:
        query = query.where(Document.object_id == object_id)
    if employee_id:
        query = query.where(Document.employee_id == employee_id)
    if q:
        term = f"%{q.strip()}%"
        query = query.where(
            or_(
                Document.document_number.ilike(term),
                Document.title.ilike(term),
                Document.description.ilike(term),
                Document.category.ilike(term),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    documents = db.scalars(
        query.order_by(Document.updated_at.desc(), Document.id).offset(offset).limit(limit)
    ).all()
    return DocumentPage(
        items=[_document_read(db, item) for item in documents],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/documents/{document_id}", response_model=DocumentDetailRead)
def get_document(
    document_id: UUID,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentDetailRead:
    document = _get_document(db, document_id)
    _ensure_document_scope(db, document, principal)
    base = _document_read(db, document).model_dump()
    versions = db.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version.desc())
    ).all()
    version_ids = [version.id for version in versions]
    approvals = (
        db.scalars(
            select(DocumentApproval)
            .where(DocumentApproval.version_id.in_(version_ids))
            .order_by(DocumentApproval.created_at.desc())
        ).all()
        if version_ids
        else []
    )
    receipts = (
        db.scalars(
            select(DocumentReadReceipt)
            .where(DocumentReadReceipt.version_id.in_(version_ids))
            .order_by(DocumentReadReceipt.read_at.desc())
        ).all()
        if version_ids
        else []
    )
    history = db.scalars(
        select(DocumentHistory)
        .where(DocumentHistory.document_id == document.id)
        .order_by(DocumentHistory.created_at.desc())
    ).all()
    return DocumentDetailRead(
        **base,
        versions=[DocumentVersionRead.model_validate(item) for item in versions],
        approvals=[DocumentApprovalRead.model_validate(item) for item in approvals],
        read_receipts=[DocumentReadReceiptRead.model_validate(item) for item in receipts],
        history=[DocumentHistoryRead.model_validate(item) for item in history],
    )


@router.post("/documents", response_model=DocumentRead, status_code=201)
def create_document(
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.create"))],
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    document_number: Annotated[str, Form()],
    title: Annotated[str, Form()],
    category: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    status_value: Annotated[str, Form(alias="status")] = "active",
    customer_id: Annotated[UUID | None, Form()] = None,
    object_id: Annotated[UUID | None, Form()] = None,
    employee_id: Annotated[UUID | None, Form()] = None,
    expires_on: Annotated[date | None, Form()] = None,
) -> DocumentRead:
    try:
        payload = DocumentCreate.model_validate(
            {
                "document_number": document_number,
                "title": title,
                "category": category,
                "description": description,
                "status": status_value,
                "customer_id": customer_id,
                "object_id": object_id,
                "employee_id": employee_id,
                "expires_on": expires_on,
            }
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False)) from exc
    safe_name, media_type, content = _upload_content(file)
    customer_id = _validate_document_links(
        db, payload.customer_id, payload.object_id, payload.employee_id
    )
    _ensure_document_link_scope(db, principal, customer_id, payload.object_id, payload.employee_id)
    document = Document(
        document_number=payload.document_number,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        status=payload.status,
        customer_id=customer_id,
        object_id=payload.object_id,
        employee_id=payload.employee_id,
        expires_on=payload.expires_on,
        created_by_id=principal.user.id,
    )
    storage_key = uuid4().hex
    try:
        db.add(document)
        db.flush()
        version = DocumentVersion(
            document_id=document.id,
            version=1,
            storage_key=storage_key,
            file_name=safe_name,
            media_type=media_type,
            size_bytes=len(content),
            sha256=sha256_hex(content),
            uploaded_by_id=principal.user.id,
        )
        db.add(version)
        store_file(storage_key, content)
        _document_history(
            db,
            document,
            principal.user.id,
            "created",
            ["document_number", "title", "category", "file"],
            {"version": 1, "size_bytes": len(content)},
        )
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="documents.uploaded",
            entity_type="document",
            entity_id=str(document.id),
            ip_address=request.client.host if request.client else None,
            details={"version": 1, "size_bytes": len(content), "sha256": version.sha256},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _remove_after_rollback(storage_key)
        raise HTTPException(
            status_code=409, detail="Dokumentnummer oder Dateiversion ist bereits vorhanden."
        ) from exc
    except OSError as exc:
        db.rollback()
        _remove_after_rollback(storage_key)
        raise HTTPException(
            status_code=500, detail="Datei konnte nicht sicher gespeichert werden."
        ) from exc
    except SQLAlchemyError:
        db.rollback()
        _remove_after_rollback(storage_key)
        raise
    db.refresh(document)
    return _document_read(db, document)


@router.post(
    "/documents/{document_id}/versions", response_model=DocumentVersionRead, status_code=201
)
def upload_document_version(
    document_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.update"))],
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
) -> DocumentVersionRead:
    document = db.scalar(select(Document).where(Document.id == document_id).with_for_update())
    if document is None or document.archived_at is not None:
        raise HTTPException(status_code=404, detail="Aktives Dokument nicht gefunden")
    _ensure_document_scope(db, document, principal)
    safe_name, media_type, content = _upload_content(file)
    latest = (
        db.scalar(
            select(func.max(DocumentVersion.version)).where(
                DocumentVersion.document_id == document.id
            )
        )
        or 0
    )
    storage_key = uuid4().hex
    version = DocumentVersion(
        document_id=document.id,
        version=latest + 1,
        storage_key=storage_key,
        file_name=safe_name,
        media_type=media_type,
        size_bytes=len(content),
        sha256=sha256_hex(content),
        uploaded_by_id=principal.user.id,
    )
    document.updated_at = _now()
    try:
        db.add(version)
        store_file(storage_key, content)
        _document_history(
            db,
            document,
            principal.user.id,
            "version_uploaded",
            ["file"],
            {"version": latest + 1, "size_bytes": len(content)},
        )
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="documents.uploaded",
            entity_type="document",
            entity_id=str(document.id),
            ip_address=request.client.host if request.client else None,
            details={"version": latest + 1, "size_bytes": len(content), "sha256": version.sha256},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _remove_after_rollback(storage_key)
        raise HTTPException(
            status_code=409, detail="Die Dokumentversion wurde parallel geändert."
        ) from exc
    except OSError as exc:
        db.rollback()
        _remove_after_rollback(storage_key)
        raise HTTPException(
            status_code=500, detail="Datei konnte nicht sicher gespeichert werden."
        ) from exc
    except SQLAlchemyError:
        db.rollback()
        _remove_after_rollback(storage_key)
        raise
    db.refresh(version)
    return DocumentVersionRead.model_validate(version)


@router.patch("/documents/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.update"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRead:
    document = _get_document(db, document_id)
    if document.archived_at is not None:
        raise HTTPException(
            status_code=409, detail="Archivierte Dokumente können nicht geändert werden."
        )
    _ensure_document_scope(db, document, principal)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Es wurden keine Änderungen übermittelt.")
    new_customer_id = changes.get("customer_id", document.customer_id)
    new_object_id = changes.get("object_id", document.object_id)
    new_employee_id = changes.get("employee_id", document.employee_id)
    changes["customer_id"] = _validate_document_links(
        db, new_customer_id, new_object_id, new_employee_id
    )
    _ensure_document_link_scope(
        db, principal, changes["customer_id"], new_object_id, new_employee_id
    )
    fields = sorted(key for key, value in changes.items() if getattr(document, key) != value)
    if not fields:
        return _document_read(db, document)
    for key in fields:
        setattr(document, key, changes[key])
    document.updated_at = _now()
    _document_history(db, document, principal.user.id, "updated", fields)
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="documents.updated",
        entity_type="document",
        entity_id=str(document.id),
        ip_address=request.client.host if request.client else None,
        details={"fields": fields},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Dokumentnummer ist bereits vergeben.") from exc
    db.refresh(document)
    return _document_read(db, document)


@router.post("/documents/{document_id}/archive", response_model=DocumentRead)
def archive_document(
    document_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.archive"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRead:
    document = _get_document(db, document_id)
    _ensure_document_scope(db, document, principal)
    if document.archived_at is not None:
        return _document_read(db, document)
    previous_status = document.status
    document.archived_at = _now()
    document.status = "archived"
    document.updated_at = document.archived_at
    _document_history(
        db,
        document,
        principal.user.id,
        "archived",
        ["status", "archived_at"],
        {"previous_status": previous_status},
    )
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="documents.archived",
        entity_type="document",
        entity_id=str(document.id),
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(document)
    return _document_read(db, document)


@router.post("/documents/{document_id}/restore", response_model=DocumentRead)
def restore_document(
    document_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.archive"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRead:
    document = _get_document(db, document_id)
    _ensure_document_scope(db, document, principal)
    if document.archived_at is None:
        return _document_read(db, document)
    last_archive = db.scalar(
        select(DocumentHistory)
        .where(
            DocumentHistory.document_id == document.id,
            DocumentHistory.action == "archived",
        )
        .order_by(DocumentHistory.created_at.desc())
        .limit(1)
    )
    previous_status = (
        last_archive.details.get("previous_status") if last_archive is not None else None
    )
    document.archived_at = None
    document.status = (
        previous_status if previous_status in {"draft", "active", "expired"} else "active"
    )
    document.updated_at = _now()
    _document_history(
        db,
        document,
        principal.user.id,
        "restored",
        ["status", "archived_at"],
        {"restored_status": document.status},
    )
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="documents.restored",
        entity_type="document",
        entity_id=str(document.id),
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(document)
    return _document_read(db, document)


@router.get("/documents/{document_id}/versions/{version_id}/download")
def download_document_version(
    document_id: UUID,
    version_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.download"))],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    document = _get_document(db, document_id)
    _ensure_document_scope(db, document, principal)
    version = _get_version(db, version_id)
    if version.document_id != document.id:
        raise HTTPException(status_code=404, detail="Dokumentversion nicht gefunden")
    try:
        content = read_file(version.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503, detail="Die Dokumentdatei ist nicht verfügbar."
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=503, detail="Der private Dokumentenspeicher ist nicht verfügbar."
        ) from exc
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="documents.downloaded",
        entity_type="document",
        entity_id=str(document.id),
        ip_address=request.client.host if request.client else None,
        details={"version": version.version, "sha256": version.sha256},
    )
    db.commit()
    safe_name = PurePosixPath(version.file_name.replace("\\", "/")).name
    disposition = f"attachment; filename*=UTF-8''{quote(safe_name, safe='')}"
    return Response(
        content=content,
        media_type=version.media_type,
        headers={
            "Content-Disposition": disposition,
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/documents/versions/{version_id}/approvals",
    response_model=DocumentApprovalRead,
    status_code=201,
)
def request_document_approval(
    version_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.update"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentApprovalRead:
    version = _get_version(db, version_id)
    document = _get_document(db, version.document_id)
    _ensure_document_scope(db, document, principal)
    existing = db.scalar(
        select(DocumentApproval.id).where(
            DocumentApproval.version_id == version.id,
            DocumentApproval.status == "pending",
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="Für diese Version liegt bereits eine Freigabeanfrage vor."
        )
    approval = DocumentApproval(
        version_id=version.id, requested_by_id=principal.user.id, status="pending"
    )
    db.add(approval)
    _document_history(
        db,
        document,
        principal.user.id,
        "approval_requested",
        [],
        {"version": version.version},
    )
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="documents.approval_requested",
        entity_type="document",
        entity_id=str(document.id),
        ip_address=request.client.host if request.client else None,
        details={"version": version.version},
    )
    db.commit()
    db.refresh(approval)
    return DocumentApprovalRead.model_validate(approval)


@router.patch("/documents/approvals/{approval_id}", response_model=DocumentApprovalRead)
def decide_document_approval(
    approval_id: UUID,
    payload: ApprovalDecision,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.approve"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentApprovalRead:
    approval = db.get(DocumentApproval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Freigabeanfrage nicht gefunden")
    version = _get_version(db, approval.version_id)
    document = _get_document(db, version.document_id)
    _ensure_document_scope(db, document, principal)
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="Diese Freigabe wurde bereits entschieden.")
    approval.status = payload.status
    approval.decision_note = payload.decision_note
    approval.decided_by_id = principal.user.id
    approval.decided_at = _now()
    _document_history(
        db,
        document,
        principal.user.id,
        f"approval_{payload.status}",
        [],
        {"version": version.version, "approval_id": str(approval.id)},
    )
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action=f"documents.approval_{payload.status}",
        entity_type="document",
        entity_id=str(document.id),
        ip_address=request.client.host if request.client else None,
        details={"version": version.version, "approval_id": str(approval.id)},
    )
    db.commit()
    db.refresh(approval)
    return DocumentApprovalRead.model_validate(approval)


@router.get("/document-approvals", response_model=list[DocumentApprovalQueueItem])
def list_document_approvals(
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.read"))],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(default="pending", alias="status"),
) -> list[DocumentApprovalQueueItem]:
    query = (
        select(DocumentApproval, Document, DocumentVersion)
        .join(DocumentVersion, DocumentVersion.id == DocumentApproval.version_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .order_by(DocumentApproval.created_at.desc())
        .limit(500)
    )
    if status_filter:
        query = query.where(DocumentApproval.status == status_filter)
    output = []
    for approval, document, version in db.execute(query):
        try:
            _ensure_document_scope(db, document, principal)
        except HTTPException as exc:
            if exc.status_code == 404:
                continue
            raise
        output.append(
            DocumentApprovalQueueItem(
                **DocumentApprovalRead.model_validate(approval).model_dump(),
                document_id=document.id,
                document_number=document.document_number,
                document_title=document.title,
                version=version.version,
            )
        )
    return output


@router.post(
    "/documents/versions/{version_id}/read-receipt", response_model=DocumentReadReceiptRead
)
def acknowledge_document_read(
    version_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("documents.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentReadReceiptRead:
    version = _get_version(db, version_id)
    document = _get_document(db, version.document_id)
    _ensure_document_scope(db, document, principal)
    receipt = db.scalar(
        select(DocumentReadReceipt).where(
            DocumentReadReceipt.version_id == version.id,
            DocumentReadReceipt.user_id == principal.user.id,
        )
    )
    if receipt is not None:
        return DocumentReadReceiptRead.model_validate(receipt)
    receipt = DocumentReadReceipt(version_id=version.id, user_id=principal.user.id)
    db.add(receipt)
    _document_history(
        db,
        document,
        principal.user.id,
        "read_confirmed",
        [],
        {"version": version.version},
    )
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="documents.read_confirmed",
        entity_type="document",
        entity_id=str(document.id),
        ip_address=request.client.host if request.client else None,
        details={"version": version.version},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        receipt = db.scalar(
            select(DocumentReadReceipt).where(
                DocumentReadReceipt.version_id == version.id,
                DocumentReadReceipt.user_id == principal.user.id,
            )
        )
        if receipt is None:
            raise
    db.refresh(receipt)
    return DocumentReadReceiptRead.model_validate(receipt)


def _contract_read(
    db: Session, contract: Contract, *, include_history: bool = False
) -> ContractRead:
    history = []
    if include_history:
        history = db.scalars(
            select(ContractHistory)
            .where(ContractHistory.contract_id == contract.id)
            .order_by(ContractHistory.created_at.desc())
        ).all()
    return ContractRead(
        id=contract.id,
        contract_number=contract.contract_number,
        name=contract.name,
        contract_type=contract.contract_type,
        counterparty=contract.counterparty,
        customer_id=contract.customer_id,
        object_id=contract.object_id,
        employee_id=contract.employee_id,
        starts_on=contract.starts_on,
        ends_on=contract.ends_on,
        notice_period_days=contract.notice_period_days,
        renewal_rule=contract.renewal_rule,
        status=contract.status,
        document_id=contract.document_id,
        internal_notes=contract.internal_notes,
        archived_at=contract.archived_at,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        history=[ContractHistoryRead.model_validate(item) for item in history],
    )


def _validate_contract_links(
    db: Session,
    customer_id: UUID,
    object_id: UUID | None,
    employee_id: UUID | None,
    document_id: UUID | None,
    contract_type: str,
) -> None:
    customer = db.get(Customer, customer_id)
    if customer is None or customer.archived_at is not None:
        raise HTTPException(status_code=422, detail="Der zugeordnete Kunde ist nicht verfügbar.")
    if object_id is not None:
        object_row = db.get(SecurityObject, object_id)
        if object_row is None or object_row.archived_at is not None:
            raise HTTPException(
                status_code=422, detail="Das zugeordnete Objekt ist nicht verfügbar."
            )
        if object_row.customer_id != customer_id:
            raise HTTPException(status_code=422, detail="Objekt und Kunde passen nicht zusammen.")
        if contract_type not in {"object", "service"}:
            raise HTTPException(
                status_code=422, detail="Dieser Vertragstyp erlaubt keine Objektzuordnung."
            )
    if employee_id is not None:
        employee = db.get(Employee, employee_id)
        if employee is None or employee.archived_at is not None:
            raise HTTPException(
                status_code=422, detail="Der zugeordnete Mitarbeiter ist nicht verfügbar."
            )
        if contract_type != "personnel":
            raise HTTPException(
                status_code=422,
                detail="Mitarbeiterzuordnung ist nur für Personalverträge zulässig.",
            )
    if document_id is not None:
        document = db.get(Document, document_id)
        if document is None or document.archived_at is not None:
            raise HTTPException(status_code=422, detail="Das Vertragsdokument ist nicht verfügbar.")


@router.get("/contracts", response_model=ContractPage)
def list_contracts(
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.read"))],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    contract_type: str | None = None,
    customer_id: UUID | None = None,
    object_id: UUID | None = None,
    include_archived: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ContractPage:
    query = _scope_contract_query(select(Contract), db, principal)
    if not include_archived or "contracts.archive" not in principal.permission_codes:
        query = query.where(Contract.archived_at.is_(None))
    if status_filter:
        query = query.where(Contract.status == status_filter)
    if contract_type:
        query = query.where(Contract.contract_type == contract_type)
    if customer_id:
        query = query.where(Contract.customer_id == customer_id)
    if object_id:
        query = query.where(Contract.object_id == object_id)
    if q:
        term = f"%{q.strip()}%"
        query = query.where(
            or_(
                Contract.contract_number.ilike(term),
                Contract.name.ilike(term),
                Contract.counterparty.ilike(term),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    contracts = db.scalars(
        query.order_by(Contract.updated_at.desc(), Contract.id).offset(offset).limit(limit)
    ).all()
    return ContractPage(
        items=[_contract_read(db, item) for item in contracts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/contracts", response_model=ContractRead, status_code=201)
def create_contract(
    payload: ContractCreate,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.create"))],
    db: Annotated[Session, Depends(get_db)],
) -> ContractRead:
    _validate_contract_links(
        db,
        payload.customer_id,
        payload.object_id,
        payload.employee_id,
        payload.document_id,
        payload.contract_type,
    )
    _ensure_contract_link_scope(
        db, principal, payload.customer_id, payload.object_id, payload.employee_id
    )
    contract = Contract(**payload.model_dump(), created_by_id=principal.user.id)
    db.add(contract)
    try:
        db.flush()
        _contract_history(
            db,
            contract,
            principal.user.id,
            "created",
            ["contract_number", "name", "contract_type", "customer_id"],
        )
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="contracts.created",
            entity_type="contract",
            entity_id=str(contract.id),
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vertragsnummer ist bereits vergeben.") from exc
    db.refresh(contract)
    return _contract_read(db, contract, include_history=True)


@router.get("/contracts/{contract_id}", response_model=ContractRead)
def get_contract(
    contract_id: UUID,
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> ContractRead:
    contract = _get_contract(db, contract_id)
    _ensure_contract_scope(db, contract, principal)
    return _contract_read(db, contract, include_history=True)


@router.patch("/contracts/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: UUID,
    payload: ContractUpdate,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.update"))],
    db: Annotated[Session, Depends(get_db)],
) -> ContractRead:
    contract = _get_contract(db, contract_id)
    if contract.archived_at is not None:
        raise HTTPException(
            status_code=409, detail="Archivierte Verträge können nicht geändert werden."
        )
    _ensure_contract_scope(db, contract, principal)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Es wurden keine Änderungen übermittelt.")
    values = {
        "customer_id": changes.get("customer_id", contract.customer_id),
        "object_id": changes.get("object_id", contract.object_id),
        "employee_id": changes.get("employee_id", contract.employee_id),
        "document_id": changes.get("document_id", contract.document_id),
        "contract_type": changes.get("contract_type", contract.contract_type),
    }
    _validate_contract_links(db, **values)
    _ensure_contract_link_scope(
        db, principal, values["customer_id"], values["object_id"], values["employee_id"]
    )
    starts_on = changes.get("starts_on", contract.starts_on)
    ends_on = changes.get("ends_on", contract.ends_on)
    if ends_on is not None and ends_on < starts_on:
        raise HTTPException(
            status_code=422, detail="Das Vertragsende darf nicht vor dem Vertragsbeginn liegen."
        )
    fields = sorted(key for key, value in changes.items() if getattr(contract, key) != value)
    if not fields:
        return _contract_read(db, contract, include_history=True)
    for key in fields:
        setattr(contract, key, changes[key])
    contract.updated_at = _now()
    _contract_history(db, contract, principal.user.id, "updated", fields)
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="contracts.updated",
        entity_type="contract",
        entity_id=str(contract.id),
        ip_address=request.client.host if request.client else None,
        details={"fields": fields},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Die Vertragsänderung ist nicht möglich."
        ) from exc
    db.refresh(contract)
    return _contract_read(db, contract, include_history=True)


@router.post("/contracts/{contract_id}/archive", response_model=ContractRead)
def archive_contract(
    contract_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.archive"))],
    db: Annotated[Session, Depends(get_db)],
) -> ContractRead:
    contract = _get_contract(db, contract_id)
    _ensure_contract_scope(db, contract, principal)
    if contract.archived_at is None:
        previous_status = contract.status
        contract.archived_at = _now()
        contract.status = "archived"
        contract.updated_at = contract.archived_at
        _contract_history(
            db,
            contract,
            principal.user.id,
            "archived",
            ["status", "archived_at"],
            {"previous_status": previous_status},
        )
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="contracts.archived",
            entity_type="contract",
            entity_id=str(contract.id),
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    db.refresh(contract)
    return _contract_read(db, contract, include_history=True)


@router.post("/contracts/{contract_id}/restore", response_model=ContractRead)
def restore_contract(
    contract_id: UUID,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.archive"))],
    db: Annotated[Session, Depends(get_db)],
) -> ContractRead:
    contract = _get_contract(db, contract_id)
    _ensure_contract_scope(db, contract, principal)
    if contract.archived_at is not None:
        last_archive = db.scalar(
            select(ContractHistory)
            .where(
                ContractHistory.contract_id == contract.id,
                ContractHistory.action == "archived",
            )
            .order_by(ContractHistory.created_at.desc())
            .limit(1)
        )
        previous_status = (
            last_archive.details.get("previous_status") if last_archive is not None else None
        )
        contract.archived_at = None
        contract.status = (
            previous_status
            if previous_status in {"draft", "active", "terminated", "expired"}
            else "active"
        )
        contract.updated_at = _now()
        _contract_history(
            db,
            contract,
            principal.user.id,
            "restored",
            ["status", "archived_at"],
            {"restored_status": contract.status},
        )
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="contracts.restored",
            entity_type="contract",
            entity_id=str(contract.id),
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    db.refresh(contract)
    return _contract_read(db, contract, include_history=True)


def _reminder_settings(db: Session) -> DocumentContractReminderSettings:
    settings = db.get(DocumentContractReminderSettings, 1)
    if settings is not None:
        return settings
    dialect = db.get_bind().dialect.name
    insert_stmt = (
        pg_insert(DocumentContractReminderSettings)
        if dialect == "postgresql"
        else sqlite_insert(DocumentContractReminderSettings)
    )
    db.execute(
        insert_stmt.values(id=1, lead_days=[90, 60, 30, 14, 7]).on_conflict_do_nothing(
            index_elements=["id"]
        )
    )
    db.flush()
    return db.get(DocumentContractReminderSettings, 1)


def _reminder_candidates(db: Session, lead_days: list[int]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    documents = db.scalars(
        select(Document).where(
            Document.archived_at.is_(None),
            Document.status.in_(("active", "draft")),
            Document.expires_on.is_not(None),
        )
    ).all()
    for document in documents:
        event_on = document.expires_on
        for days in lead_days:
            remind_on = date.fromordinal(event_on.toordinal() - days)
            candidates.append(
                {
                    "id": uuid4(),
                    "document_id": document.id,
                    "contract_id": None,
                    "reminder_type": "document_expiry",
                    "event_on": event_on,
                    "remind_on": remind_on,
                    "deduplication_key": (
                        f"document:{document.id}:document_expiry:{event_on.isoformat()}:{remind_on.isoformat()}"
                    ),
                    "status": "open",
                }
            )

    contracts = db.scalars(
        select(Contract).where(
            Contract.archived_at.is_(None),
            Contract.status == "active",
            Contract.ends_on.is_not(None),
        )
    ).all()
    for contract in contracts:
        event_list: list[tuple[str, date]] = [("contract_expiry", contract.ends_on)]
        if contract.notice_period_days is not None:
            notice_date = date.fromordinal(
                contract.ends_on.toordinal() - contract.notice_period_days
            )
            event_list.append(("contract_termination", notice_date))
        if contract.renewal_rule:
            event_list.append(("contract_renewal", contract.ends_on))
        for reminder_type, event_on in event_list:
            for days in lead_days:
                remind_on = date.fromordinal(event_on.toordinal() - days)
                candidates.append(
                    {
                        "id": uuid4(),
                        "document_id": None,
                        "contract_id": contract.id,
                        "reminder_type": reminder_type,
                        "event_on": event_on,
                        "remind_on": remind_on,
                        "deduplication_key": (
                            f"contract:{contract.id}:{reminder_type}:{event_on.isoformat()}:{remind_on.isoformat()}"
                        ),
                        "status": "open",
                    }
                )
    return candidates


def _generate_reminders(db: Session, principal: AuthPrincipal) -> int:
    settings = _reminder_settings(db)
    candidates = _reminder_candidates(db, settings.lead_days)
    expected_keys = {item["deduplication_key"] for item in candidates}
    stale_reminders = db.scalars(
        select(DocumentContractReminder).where(DocumentContractReminder.status == "open")
    ).all()
    dismissed = 0
    for reminder in stale_reminders:
        if reminder.deduplication_key not in expected_keys:
            reminder.status = "dismissed"
            dismissed += 1

    created = 0
    if candidates:
        dialect = db.get_bind().dialect.name
        insert_stmt = (
            pg_insert(DocumentContractReminder)
            if dialect == "postgresql"
            else sqlite_insert(DocumentContractReminder)
        )
        result = db.execute(
            insert_stmt.values(candidates).on_conflict_do_nothing(
                index_elements=["deduplication_key"]
            )
        )
        created = result.rowcount or 0
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="contracts.reminders_generated",
        entity_type="document_contract_reminder",
        details={"created": created, "obsolete_dismissed": dismissed},
    )
    db.commit()
    return created


def _reminder_read(db: Session, reminder: DocumentContractReminder) -> ReminderRead:
    if reminder.document_id is not None:
        document = db.get(Document, reminder.document_id)
        subject = document.title if document else "Dokument"
        number = document.document_number if document else ""
    else:
        contract = db.get(Contract, reminder.contract_id)
        subject = contract.name if contract else "Vertrag"
        number = contract.contract_number if contract else ""
    return ReminderRead(
        id=reminder.id,
        document_id=reminder.document_id,
        contract_id=reminder.contract_id,
        reminder_type=reminder.reminder_type,
        event_on=reminder.event_on,
        remind_on=reminder.remind_on,
        status=reminder.status,
        created_at=reminder.created_at,
        subject=subject,
        number=number,
    )


@router.get("/reminders/settings", response_model=ReminderSettingsRead)
def get_reminder_settings(
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.manage_reminders"))],
    db: Annotated[Session, Depends(get_db)],
) -> ReminderSettingsRead:
    settings = _reminder_settings(db)
    db.commit()
    return ReminderSettingsRead(
        lead_days=settings.lead_days,
        updated_by_id=settings.updated_by_id,
        updated_at=settings.updated_at,
    )


@router.put("/reminders/settings", response_model=ReminderSettingsRead)
def update_reminder_settings(
    payload: ReminderSettingsUpdate,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.manage_reminders"))],
    db: Annotated[Session, Depends(get_db)],
) -> ReminderSettingsRead:
    settings = _reminder_settings(db)
    if settings.lead_days != payload.lead_days:
        settings.lead_days = payload.lead_days
        settings.updated_by_id = principal.user.id
        settings.updated_at = _now()
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="contracts.reminder_settings_updated",
            entity_type="document_contract_reminder_settings",
            entity_id="1",
            ip_address=request.client.host if request.client else None,
            details={"lead_days": payload.lead_days},
        )
        db.commit()
    return ReminderSettingsRead(
        lead_days=settings.lead_days,
        updated_by_id=settings.updated_by_id,
        updated_at=settings.updated_at,
    )


@router.post("/reminders/generate", response_model=dict[str, int])
def generate_reminders(
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.manage_reminders"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int]:
    return {"created": _generate_reminders(db, principal)}


@router.get("/reminders", response_model=list[ReminderRead])
def list_reminders(
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.read"))],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(default="open", alias="status"),
    due_before: date | None = None,
) -> list[ReminderRead]:
    query = select(DocumentContractReminder)
    if status_filter:
        query = query.where(DocumentContractReminder.status == status_filter)
    if due_before:
        query = query.where(DocumentContractReminder.remind_on <= due_before)
    reminders = db.scalars(
        query.order_by(
            DocumentContractReminder.remind_on,
            DocumentContractReminder.event_on,
        ).limit(500)
    ).all()
    visible = []
    for reminder in reminders:
        if reminder.document_id is not None:
            document = db.get(Document, reminder.document_id)
            if document is None:
                continue
            try:
                _ensure_document_scope(db, document, principal)
            except HTTPException as exc:
                if exc.status_code == 404:
                    continue
                raise
        else:
            contract = db.get(Contract, reminder.contract_id)
            if contract is None:
                continue
            try:
                _ensure_contract_scope(db, contract, principal)
            except HTTPException as exc:
                if exc.status_code == 404:
                    continue
                raise
        visible.append(_reminder_read(db, reminder))
    return visible


@router.patch("/reminders/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: UUID,
    payload: ReminderStatusUpdate,
    request: Request,
    principal: Annotated[AuthPrincipal, Depends(require_permission("contracts.manage_reminders"))],
    db: Annotated[Session, Depends(get_db)],
) -> ReminderRead:
    reminder = db.get(DocumentContractReminder, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Erinnerung nicht gefunden")
    if reminder.document_id is not None:
        document = _get_document(db, reminder.document_id)
        _ensure_document_scope(db, document, principal)
    else:
        contract = _get_contract(db, reminder.contract_id)
        _ensure_contract_scope(db, contract, principal)
    reminder.status = payload.status
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action=f"contracts.reminder_{payload.status}",
        entity_type="document_contract_reminder",
        entity_id=str(reminder.id),
        ip_address=request.client.host if request.client else None,
        details={
            "reminder_type": reminder.reminder_type,
            "remind_on": reminder.remind_on.isoformat(),
        },
    )
    db.commit()
    db.refresh(reminder)
    return _reminder_read(db, reminder)
