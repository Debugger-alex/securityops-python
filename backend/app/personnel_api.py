from datetime import UTC, date, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import add_audit_entry, require_permission
from app.database import get_db
from app.models import (
    Employee,
    EmployeeAbsence,
    EmployeeHistory,
    EmployeeQualification,
    EmployeeSensitiveDetails,
    User,
)
from app.schemas import (
    EmployeeAbsenceCreate,
    EmployeeAbsenceRead,
    EmployeeAbsenceUpdate,
    EmployeeCreate,
    EmployeeHistoryRead,
    EmployeePage,
    EmployeeQualificationCreate,
    EmployeeQualificationExpiringRead,
    EmployeeQualificationRead,
    EmployeeQualificationUpdate,
    EmployeeRead,
    EmployeeSensitiveRead,
    EmployeeSensitiveUpdate,
    EmployeeStatus,
    EmployeeUpdate,
)

router = APIRouter()


def employee_query():
    return select(Employee).options(selectinload(Employee.user))


def get_employee_or_404(db: Session, employee_id: UUID) -> Employee:
    employee = db.scalar(employee_query().where(Employee.id == employee_id))
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mitarbeiter nicht gefunden"
        )
    return employee


def ensure_employee_is_active(employee: Employee) -> None:
    if employee.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archivierte Mitarbeiter müssen vor Änderungen reaktiviert werden",
        )


def validate_linked_user(db: Session, user_id: UUID | None) -> User | None:
    if user_id is None:
        return None
    user = db.scalar(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id, User.is_active.is_(True))
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Das verknüpfte Benutzerkonto muss vorhanden und aktiv sein",
        )
    if not any(role.code in {"employee", "object_manager"} for role in user.roles):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Das verknüpfte Konto benötigt eine Mitarbeiter- oder Objektleitungsrolle",
        )
    return user


def record_employee_event(
    db: Session,
    *,
    employee: Employee,
    actor_id: UUID,
    action: str,
    changed_fields: set[str],
    ip_address: str | None,
) -> None:
    sorted_fields = sorted(changed_fields)
    db.add(
        EmployeeHistory(
            employee_id=employee.id,
            actor_id=actor_id,
            action=action,
            changed_fields=sorted_fields,
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"employees.{action}",
        entity_type="employee",
        entity_id=str(employee.id),
        ip_address=ip_address,
        details={"fields": sorted_fields},
    )


def commit_employee_transaction(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Die Personaländerung verletzt eine Datenbankbedingung",
        ) from exc


def flush_employee_transaction(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Die Personaländerung verletzt eine Datenbankbedingung",
        ) from exc


def validate_employee_dates(hired_on: date, ended_on: date | None) -> None:
    if ended_on is not None and ended_on < hired_on:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Das Austrittsdatum darf nicht vor dem Eintrittsdatum liegen",
        )


def employee_absence_query(employee_id: UUID):
    return select(EmployeeAbsence).where(EmployeeAbsence.employee_id == employee_id)


@router.get("/employees", response_model=EmployeePage)
def list_employees(
    q: str | None = Query(default=None, max_length=200),
    employment_status: EmployeeStatus | None = Query(default=None, alias="status"),
    include_archived: bool = False,
    sort_by: Literal["employee_number", "full_name", "hired_on", "employment_status"] = "full_name",
    sort_order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("employees.read")),
) -> EmployeePage:
    query = employee_query()
    count_query = select(func.count()).select_from(Employee)
    filters = []
    if not include_archived:
        filters.append(Employee.archived_at.is_(None))
    if employment_status is not None:
        filters.append(Employee.employment_status == employment_status)
    if q and q.strip():
        term = f"%{q.strip()}%"
        filters.append(
            or_(
                Employee.employee_number.ilike(term),
                Employee.full_name.ilike(term),
                Employee.email.ilike(term),
                Employee.phone.ilike(term),
                Employee.job_title.ilike(term),
            )
        )
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
    sort_columns = {
        "employee_number": Employee.employee_number,
        "full_name": Employee.full_name,
        "hired_on": Employee.hired_on,
        "employment_status": Employee.employment_status,
    }
    ordering = sort_columns[sort_by].asc() if sort_order == "asc" else sort_columns[sort_by].desc()
    employees = db.scalars(
        query.order_by(ordering, Employee.employee_number).limit(limit).offset(offset)
    ).all()
    return EmployeePage(
        items=[EmployeeRead.model_validate(employee) for employee in employees],
        total=db.scalar(count_query) or 0,
        limit=limit,
        offset=offset,
    )


@router.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    request: Request,
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.manage")),
) -> EmployeeRead:
    validate_employee_dates(payload.hired_on, payload.ended_on)
    validate_linked_user(db, payload.user_id)
    if (
        db.scalar(select(Employee.id).where(Employee.employee_number == payload.employee_number))
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Die Personalnummer ist bereits vergeben",
        )
    employee = Employee(
        employee_number=payload.employee_number,
        user_id=payload.user_id,
        full_name=payload.full_name,
        email=str(payload.email).lower() if payload.email else None,
        phone=payload.phone,
        job_title=payload.job_title,
        employment_status=payload.employment_status,
        hired_on=payload.hired_on,
        ended_on=payload.ended_on,
        contract_type=payload.contract_type,
        weekly_hours=payload.weekly_hours,
    )
    db.add(employee)
    flush_employee_transaction(db)
    record_employee_event(
        db,
        employee=employee,
        actor_id=principal.user.id,
        action="created",
        changed_fields={
            field for field, value in payload.model_dump().items() if value is not None
        },
        ip_address=request.client.host if request.client else None,
    )
    commit_employee_transaction(db)
    return EmployeeRead.model_validate(get_employee_or_404(db, employee.id))


@router.get(
    "/employees/qualifications/expiring", response_model=list[EmployeeQualificationExpiringRead]
)
def list_expiring_qualifications(
    days: int = Query(default=30, ge=0, le=365),
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("employees.read")),
) -> list[EmployeeQualificationExpiringRead]:
    today = date.today()
    rows = db.execute(
        select(EmployeeQualification, Employee.employee_number, Employee.full_name)
        .join(Employee, Employee.id == EmployeeQualification.employee_id)
        .where(
            Employee.archived_at.is_(None),
            Employee.employment_status != "terminated",
            EmployeeQualification.archived_at.is_(None),
            EmployeeQualification.expires_on.is_not(None),
            EmployeeQualification.expires_on <= today + timedelta(days=days),
        )
        .order_by(EmployeeQualification.expires_on, Employee.full_name)
    ).all()
    return [
        EmployeeQualificationExpiringRead(
            **EmployeeQualificationRead.model_validate(qualification).model_dump(),
            employee_number=employee_number,
            employee_name=employee_name,
            days_until_expiry=(qualification.expires_on - today).days,
        )
        for qualification, employee_number, employee_name in rows
    ]


@router.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("employees.read")),
) -> EmployeeRead:
    return EmployeeRead.model_validate(get_employee_or_404(db, employee_id))


@router.patch("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(
    request: Request,
    employee_id: UUID,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.manage")),
) -> EmployeeRead:
    employee = get_employee_or_404(db, employee_id)
    ensure_employee_is_active(employee)
    changes = payload.model_dump(exclude_unset=True)
    hired_on = changes.get("hired_on", employee.hired_on)
    ended_on = changes.get("ended_on", employee.ended_on)
    validate_employee_dates(hired_on, ended_on)
    if "user_id" in changes:
        validate_linked_user(db, changes["user_id"])
    if (
        "employee_number" in changes
        and changes["employee_number"] != employee.employee_number
        and db.scalar(
            select(Employee.id).where(
                Employee.employee_number == changes["employee_number"],
                Employee.id != employee.id,
            )
        )
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Die Personalnummer ist bereits vergeben",
        )

    changed_fields = set()
    for field, value in changes.items():
        if field == "email" and value is not None:
            value = str(value).lower()
        if getattr(employee, field) != value:
            setattr(employee, field, value)
            changed_fields.add(field)
    if changed_fields:
        record_employee_event(
            db,
            employee=employee,
            actor_id=principal.user.id,
            action="updated",
            changed_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
        )
        commit_employee_transaction(db)
    return EmployeeRead.model_validate(get_employee_or_404(db, employee.id))


@router.post("/employees/{employee_id}/archive", response_model=EmployeeRead)
def archive_employee(
    request: Request,
    employee_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.manage")),
) -> EmployeeRead:
    employee = get_employee_or_404(db, employee_id)
    if employee.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mitarbeiter ist bereits archiviert",
        )
    employee.archived_at = datetime.now(UTC)
    record_employee_event(
        db,
        employee=employee,
        actor_id=principal.user.id,
        action="archived",
        changed_fields={"archived_at"},
        ip_address=request.client.host if request.client else None,
    )
    commit_employee_transaction(db)
    return EmployeeRead.model_validate(get_employee_or_404(db, employee.id))


@router.post("/employees/{employee_id}/reactivate", response_model=EmployeeRead)
def reactivate_employee(
    request: Request,
    employee_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.manage")),
) -> EmployeeRead:
    employee = get_employee_or_404(db, employee_id)
    if employee.archived_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mitarbeiter ist nicht archiviert",
        )
    employee.archived_at = None
    record_employee_event(
        db,
        employee=employee,
        actor_id=principal.user.id,
        action="reactivated",
        changed_fields={"archived_at"},
        ip_address=request.client.host if request.client else None,
    )
    commit_employee_transaction(db)
    return EmployeeRead.model_validate(get_employee_or_404(db, employee.id))


@router.get("/employees/{employee_id}/sensitive", response_model=EmployeeSensitiveRead)
def get_employee_sensitive_details(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("employees.sensitive.read")),
) -> EmployeeSensitiveRead:
    employee = get_employee_or_404(db, employee_id)
    details = db.get(EmployeeSensitiveDetails, employee.id)
    return EmployeeSensitiveRead(
        employee_id=employee.id,
        address=details.address if details else None,
        emergency_contact=details.emergency_contact if details else None,
        internal_notes=details.internal_notes if details else None,
        updated_at=details.updated_at if details else None,
    )


@router.patch("/employees/{employee_id}/sensitive", response_model=EmployeeSensitiveRead)
def update_employee_sensitive_details(
    request: Request,
    employee_id: UUID,
    payload: EmployeeSensitiveUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.sensitive.manage")),
) -> EmployeeSensitiveRead:
    employee = get_employee_or_404(db, employee_id)
    ensure_employee_is_active(employee)
    changes = payload.model_dump(exclude_unset=True)
    details = db.get(EmployeeSensitiveDetails, employee.id)
    changed_fields = {
        field for field, value in changes.items() if details is None and value is not None
    }
    if details is None and changed_fields:
        details = EmployeeSensitiveDetails(employee_id=employee.id)
        db.add(details)
        flush_employee_transaction(db)
    if details is not None:
        for field, value in changes.items():
            if getattr(details, field) != value:
                setattr(details, field, value)
                changed_fields.add(field)
    if changed_fields:
        record_employee_event(
            db,
            employee=employee,
            actor_id=principal.user.id,
            action="sensitive_updated",
            changed_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
        )
        commit_employee_transaction(db)
    details = db.get(EmployeeSensitiveDetails, employee.id)
    return EmployeeSensitiveRead(
        employee_id=employee.id,
        address=details.address if details else None,
        emergency_contact=details.emergency_contact if details else None,
        internal_notes=details.internal_notes if details else None,
        updated_at=details.updated_at if details else None,
    )


@router.get(
    "/employees/{employee_id}/qualifications", response_model=list[EmployeeQualificationRead]
)
def list_employee_qualifications(
    employee_id: UUID,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("employees.read")),
) -> list[EmployeeQualificationRead]:
    get_employee_or_404(db, employee_id)
    query = select(EmployeeQualification).where(EmployeeQualification.employee_id == employee_id)
    if not include_archived:
        query = query.where(EmployeeQualification.archived_at.is_(None))
    qualifications = db.scalars(
        query.order_by(EmployeeQualification.expires_on, EmployeeQualification.name)
    ).all()
    return [EmployeeQualificationRead.model_validate(item) for item in qualifications]


@router.post(
    "/employees/{employee_id}/qualifications",
    response_model=EmployeeQualificationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_employee_qualification(
    request: Request,
    employee_id: UUID,
    payload: EmployeeQualificationCreate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.manage")),
) -> EmployeeQualificationRead:
    employee = get_employee_or_404(db, employee_id)
    ensure_employee_is_active(employee)
    qualification = EmployeeQualification(employee_id=employee.id, **payload.model_dump())
    db.add(qualification)
    flush_employee_transaction(db)
    record_employee_event(
        db,
        employee=employee,
        actor_id=principal.user.id,
        action="qualification_created",
        changed_fields={"qualifications"},
        ip_address=request.client.host if request.client else None,
    )
    commit_employee_transaction(db)
    return EmployeeQualificationRead.model_validate(qualification)


@router.patch(
    "/employees/{employee_id}/qualifications/{qualification_id}",
    response_model=EmployeeQualificationRead,
)
def update_employee_qualification(
    request: Request,
    employee_id: UUID,
    qualification_id: UUID,
    payload: EmployeeQualificationUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.manage")),
) -> EmployeeQualificationRead:
    employee = get_employee_or_404(db, employee_id)
    ensure_employee_is_active(employee)
    qualification = db.scalar(
        select(EmployeeQualification).where(
            EmployeeQualification.id == qualification_id,
            EmployeeQualification.employee_id == employee_id,
        )
    )
    if qualification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qualifikationsnachweis nicht gefunden",
        )
    if qualification.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archivierte Nachweise können nicht geändert werden",
        )
    changes = payload.model_dump(exclude_unset=True)
    valid_from = changes.get("valid_from", qualification.valid_from)
    expires_on = changes.get("expires_on", qualification.expires_on)
    if valid_from is not None and expires_on is not None and expires_on < valid_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Das Ablaufdatum darf nicht vor dem Gültigkeitsbeginn liegen",
        )
    changed_fields = set()
    for field, value in changes.items():
        if getattr(qualification, field) != value:
            setattr(qualification, field, value)
            changed_fields.add(field)
    if changed_fields:
        record_employee_event(
            db,
            employee=employee,
            actor_id=principal.user.id,
            action="qualification_updated",
            changed_fields={"qualifications"},
            ip_address=request.client.host if request.client else None,
        )
        commit_employee_transaction(db)
    return EmployeeQualificationRead.model_validate(qualification)


@router.post(
    "/employees/{employee_id}/qualifications/{qualification_id}/archive",
    response_model=EmployeeQualificationRead,
)
def archive_employee_qualification(
    request: Request,
    employee_id: UUID,
    qualification_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.manage")),
) -> EmployeeQualificationRead:
    employee = get_employee_or_404(db, employee_id)
    ensure_employee_is_active(employee)
    qualification = db.scalar(
        select(EmployeeQualification).where(
            EmployeeQualification.id == qualification_id,
            EmployeeQualification.employee_id == employee_id,
        )
    )
    if qualification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qualifikationsnachweis nicht gefunden",
        )
    if qualification.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Qualifikationsnachweis ist bereits archiviert",
        )
    qualification.archived_at = datetime.now(UTC)
    record_employee_event(
        db,
        employee=employee,
        actor_id=principal.user.id,
        action="qualification_archived",
        changed_fields={"qualifications"},
        ip_address=request.client.host if request.client else None,
    )
    commit_employee_transaction(db)
    return EmployeeQualificationRead.model_validate(qualification)


@router.get(
    "/employees/{employee_id}/absences",
    response_model=list[EmployeeAbsenceRead],
)
def list_employee_absences(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("employees.absences.read")),
) -> list[EmployeeAbsenceRead]:
    get_employee_or_404(db, employee_id)
    absences = db.scalars(
        employee_absence_query(employee_id).order_by(
            EmployeeAbsence.starts_on.desc(), EmployeeAbsence.created_at.desc()
        )
    ).all()
    return [EmployeeAbsenceRead.model_validate(item) for item in absences]


@router.post(
    "/employees/{employee_id}/absences",
    response_model=EmployeeAbsenceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_employee_absence(
    request: Request,
    employee_id: UUID,
    payload: EmployeeAbsenceCreate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.absences.manage")),
) -> EmployeeAbsenceRead:
    employee = get_employee_or_404(db, employee_id)
    ensure_employee_is_active(employee)
    absence = EmployeeAbsence(
        employee_id=employee.id,
        created_by_id=principal.user.id,
        **payload.model_dump(),
    )
    db.add(absence)
    flush_employee_transaction(db)
    record_employee_event(
        db,
        employee=employee,
        actor_id=principal.user.id,
        action="absence_created",
        changed_fields={"absences"},
        ip_address=request.client.host if request.client else None,
    )
    commit_employee_transaction(db)
    return EmployeeAbsenceRead.model_validate(absence)


@router.patch(
    "/employees/{employee_id}/absences/{absence_id}",
    response_model=EmployeeAbsenceRead,
)
def update_employee_absence(
    request: Request,
    employee_id: UUID,
    absence_id: UUID,
    payload: EmployeeAbsenceUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("employees.absences.manage")),
) -> EmployeeAbsenceRead:
    employee = get_employee_or_404(db, employee_id)
    ensure_employee_is_active(employee)
    absence = db.scalar(employee_absence_query(employee_id).where(EmployeeAbsence.id == absence_id))
    if absence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abwesenheit nicht gefunden",
        )
    changes = payload.model_dump(exclude_unset=True)
    starts_on = changes.get("starts_on", absence.starts_on)
    ends_on = changes.get("ends_on", absence.ends_on)
    if ends_on < starts_on:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Das Abwesenheitsende darf nicht vor dem Beginn liegen",
        )
    changed_fields = set()
    for field, value in changes.items():
        if getattr(absence, field) != value:
            setattr(absence, field, value)
            changed_fields.add(field)
    if changed_fields:
        record_employee_event(
            db,
            employee=employee,
            actor_id=principal.user.id,
            action="absence_updated",
            changed_fields={"absences"},
            ip_address=request.client.host if request.client else None,
        )
        commit_employee_transaction(db)
    return EmployeeAbsenceRead.model_validate(absence)


@router.get("/employees/{employee_id}/history", response_model=list[EmployeeHistoryRead])
def list_employee_history(
    employee_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("employees.read")),
) -> list[EmployeeHistoryRead]:
    get_employee_or_404(db, employee_id)
    history = db.scalars(
        select(EmployeeHistory)
        .where(EmployeeHistory.employee_id == employee_id)
        .order_by(EmployeeHistory.created_at.desc(), EmployeeHistory.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return [EmployeeHistoryRead.model_validate(item) for item in history]
