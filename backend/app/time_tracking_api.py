import csv
import io
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth import AuthPrincipal, add_audit_entry, get_auth_principal
from app.database import get_db
from app.models import (
    Employee,
    ObjectAssignment,
    ScheduleShift,
    SecurityObject,
    TimeEntry,
    TimeEntryCorrection,
    TimeEntryCorrectionSegment,
    TimeEntryHistory,
    TimeEntrySegment,
)
from app.scheduling_api import as_utc, get_schedule_settings, get_zone, lock_employee_schedule
from app.schemas import (
    MissingShiftRead,
    TimeCorrectionCreate,
    TimeEntryCorrectionRead,
    TimeEntryDecision,
    TimeEntryManualCreate,
    TimeEntryRead,
    TimeEntryReportGroup,
    TimeEntrySegmentRead,
    TimeEntryStart,
    TimeEntrySummaryRead,
)
from app.time_tracking_surcharges import (
    ensure_interval_not_period_locked,
    lock_time_tracking_periods,
)

router = APIRouter()


def now_utc() -> datetime:
    return datetime.now(UTC)


def current_employee(db: Session, principal: AuthPrincipal) -> Employee:
    employee = db.scalar(select(Employee).where(Employee.user_id == principal.user.id))
    if employee is None or employee.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Für dieses Benutzerkonto ist keine aktive Personalakte verknüpft.",
        )
    return employee


def visible_entry_query(principal: AuthPrincipal):
    query = (
        select(TimeEntry)
        .join(Employee, TimeEntry.employee_id == Employee.id)
        .join(SecurityObject, TimeEntry.object_id == SecurityObject.id)
        .options(
            joinedload(TimeEntry.employee),
            joinedload(TimeEntry.object).joinedload(SecurityObject.customer),
            joinedload(TimeEntry.shift),
            selectinload(TimeEntry.segments),
            selectinload(TimeEntry.corrections).selectinload(TimeEntryCorrection.segments),
        )
    )
    permissions = principal.permission_codes
    if "time_tracking.read_all" not in permissions:
        query = query.where(Employee.user_id == principal.user.id)
    if "objects.read_all" not in permissions:
        query = query.where(
            SecurityObject.assignments.any(ObjectAssignment.user_id == principal.user.id)
        )
    return query


def get_entry(
    db: Session,
    entry_id: UUID,
    principal: AuthPrincipal,
    *,
    for_update: bool = False,
) -> TimeEntry:
    query = visible_entry_query(principal).where(TimeEntry.id == entry_id)
    if for_update:
        query = query.with_for_update(of=TimeEntry)
    entry = db.scalar(query)
    if entry is None:
        raise HTTPException(status_code=404, detail="Arbeitszeitbuchung nicht gefunden.")
    return entry


def get_object_for_user(db: Session, object_id: UUID, principal: AuthPrincipal) -> SecurityObject:
    query = select(SecurityObject).where(
        SecurityObject.id == object_id,
        SecurityObject.status == "active",
        SecurityObject.archived_at.is_(None),
    )
    if "objects.manage_all" not in principal.permission_codes:
        query = query.where(
            SecurityObject.assignments.any(ObjectAssignment.user_id == principal.user.id)
        )
    obj = db.scalar(query)
    if obj is None:
        raise HTTPException(
            status_code=404, detail="Aktives oder zugewiesenes Objekt nicht gefunden."
        )
    return obj


def employee_object_assignment(db: Session, employee: Employee, obj: SecurityObject) -> bool:
    if employee.user_id is None:
        return False
    return (
        db.scalar(
            select(ObjectAssignment.id).where(
                ObjectAssignment.object_id == obj.id,
                ObjectAssignment.user_id == employee.user_id,
            )
        )
        is not None
    )


def require_employee_object_assignment(
    db: Session, employee: Employee, obj: SecurityObject
) -> None:
    if employee.archived_at is not None or employee.employment_status != "active":
        raise HTTPException(status_code=409, detail="Der Mitarbeiter ist nicht aktiv beschäftigt.")
    if not employee_object_assignment(db, employee, obj):
        raise HTTPException(
            status_code=409,
            detail="Der Mitarbeiter ist dem ausgewählten Objekt nicht zugewiesen.",
        )


def add_history(
    db: Session,
    *,
    entry: TimeEntry,
    actor_id: UUID,
    action: str,
    request: Request,
    details: dict[str, object] | None = None,
) -> None:
    safe_details = details or {}
    db.add(
        TimeEntryHistory(
            entry_id=entry.id,
            actor_id=actor_id,
            action=action,
            details=safe_details,
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"time_tracking.{action}",
        entity_type="time_entry",
        entity_id=str(entry.id),
        ip_address=request.client.host if request.client else None,
        details=safe_details,
    )


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Die Arbeitszeitbuchung kollidiert mit einer bestehenden Buchung.",
        ) from exc


def flush_or_conflict(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Die Arbeitszeitbuchung kollidiert mit einer bestehenden Buchung.",
        ) from exc


def segment_end(segment: TimeEntrySegment, fallback: datetime | None = None) -> datetime | None:
    if segment.ended_at is not None:
        return as_utc(segment.ended_at)
    return as_utc(fallback) if fallback is not None else None


def approved_correction(entry: TimeEntry) -> TimeEntryCorrection | None:
    approved = [item for item in entry.corrections if item.status == "approved"]
    return (
        max(approved, key=lambda item: (as_utc(item.decided_at), str(item.id)))
        if approved
        else None
    )


def effective_segment_values(
    entry: TimeEntry,
) -> list[tuple[UUID, int, str, datetime, datetime | None]]:
    correction = approved_correction(entry)
    if correction:
        return [
            (
                segment.id,
                segment.position,
                segment.kind,
                as_utc(segment.started_at),
                as_utc(segment.ended_at),
            )
            for segment in correction.segments
        ]
    return [
        (
            segment.id,
            segment.position,
            segment.kind,
            as_utc(segment.started_at),
            as_utc(segment.ended_at) if segment.ended_at is not None else None,
        )
        for segment in entry.segments
    ]


def read_correction(correction: TimeEntryCorrection) -> TimeEntryCorrectionRead:
    return TimeEntryCorrectionRead(
        id=correction.id,
        entry_id=correction.entry_id,
        reason=correction.reason,
        status=correction.status,
        rejection_reason=correction.rejection_reason,
        requested_by_id=correction.requested_by_id,
        decided_by_id=correction.decided_by_id,
        requested_at=as_utc(correction.requested_at),
        decided_at=as_utc(correction.decided_at) if correction.decided_at else None,
        segments=[
            TimeEntrySegmentRead(
                id=segment.id,
                position=segment.position,
                kind=segment.kind,
                started_at=as_utc(segment.started_at),
                ended_at=as_utc(segment.ended_at),
            )
            for segment in correction.segments
        ],
    )


def read_entry(entry: TimeEntry, time_zone: str) -> TimeEntryRead:
    values = effective_segment_values(entry)
    now = now_utc()
    actual_work = sum(
        ((end or now) - start for _, _, kind, start, end in values if kind == "work"),
        timedelta(),
    )
    actual_break = sum(
        ((end or now) - start for _, _, kind, start, end in values if kind == "break"),
        timedelta(),
    )
    started_at = values[0][3] if values else as_utc(entry.started_at)
    ended_at = values[-1][4] if values and values[-1][4] is not None else None
    planned_start = as_utc(entry.shift.starts_at) if entry.shift else None
    planned_end = as_utc(entry.shift.ends_at) if entry.shift else None
    planned_break = entry.shift.break_minutes * 60 if entry.shift else 0
    planned_work = (
        max(0, int((planned_end - planned_start).total_seconds()) - planned_break)
        if planned_start and planned_end
        else None
    )
    actual_seconds = actual_work.total_seconds()
    return TimeEntryRead(
        id=entry.id,
        employee_id=entry.employee_id,
        employee_number=entry.employee.employee_number,
        employee_name=entry.employee.full_name,
        object_id=entry.object_id,
        object_code=entry.object.code,
        object_name=entry.object.name,
        customer_id=entry.object.customer_id,
        customer_name=entry.object.customer.company_name,
        shift_id=entry.shift_id,
        planned_start_at=planned_start,
        planned_end_at=planned_end,
        planned_break_seconds=planned_break,
        time_zone=time_zone,
        started_at=started_at,
        ended_at=ended_at,
        status=entry.status,
        actual_work_seconds=actual_seconds,
        actual_break_seconds=actual_break.total_seconds(),
        planned_work_seconds=planned_work,
        difference_seconds=actual_seconds - planned_work if planned_work is not None else None,
        start_deviation_seconds=(started_at - planned_start).total_seconds()
        if planned_start
        else None,
        end_deviation_seconds=(ended_at - planned_end).total_seconds()
        if ended_at and planned_end
        else None,
        created_by_id=entry.created_by_id,
        submitted_at=as_utc(entry.submitted_at) if entry.submitted_at else None,
        reviewed_by_id=entry.reviewed_by_id,
        reviewed_at=as_utc(entry.reviewed_at) if entry.reviewed_at else None,
        decision_reason=entry.decision_reason,
        segments=[
            TimeEntrySegmentRead(
                id=segment_id,
                position=position,
                kind=kind,
                started_at=start,
                ended_at=end,
            )
            for segment_id, position, kind, start, end in values
        ],
        corrections=[
            read_correction(item)
            for item in sorted(
                entry.corrections, key=lambda item: (as_utc(item.requested_at), str(item.id))
            )
        ],
    )


def validate_segments(
    segments,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[datetime, datetime]:
    if not segments:
        raise HTTPException(
            status_code=422, detail="Mindestens ein Arbeitszeitsegment ist erforderlich."
        )
    for index, segment in enumerate(segments):
        expected = "work" if index % 2 == 0 else "break"
        if segment.kind != expected:
            raise HTTPException(
                status_code=422,
                detail="Arbeits- und Pausensegmente müssen sich abwechseln und mit Arbeit beginnen.",
            )
        if index and segments[index - 1].ended_at != segment.started_at:
            raise HTTPException(
                status_code=422,
                detail="Arbeits- und Pausensegmente müssen lückenlos aufeinanderfolgen.",
            )
    first = segments[0].started_at.astimezone(UTC)
    last = segments[-1].ended_at.astimezone(UTC)
    if start is not None and first != as_utc(start):
        raise HTTPException(
            status_code=422, detail="Der erste Abschnitt muss zum Dienstbeginn passen."
        )
    if end is not None and last != as_utc(end):
        raise HTTPException(
            status_code=422, detail="Der letzte Abschnitt muss zum Dienstende passen."
        )
    return first, last


def correction_segments_for_entry(entry: TimeEntry) -> list[tuple[str, datetime, datetime | None]]:
    values = effective_segment_values(entry)
    return [(kind, start, end) for _, _, kind, start, end in values]


def ensure_no_work_overlap(
    db: Session,
    employee_id: UUID,
    proposed: list[tuple[str, datetime, datetime]],
    *,
    exclude_entry_id: UUID | None = None,
) -> None:
    proposed_work = [(start, end) for kind, start, end in proposed if kind == "work"]
    if not proposed_work:
        raise HTTPException(status_code=422, detail="Die Buchung muss Arbeitszeit enthalten.")
    query = (
        select(TimeEntry)
        .where(TimeEntry.employee_id == employee_id, TimeEntry.status != "open")
        .options(
            selectinload(TimeEntry.segments),
            selectinload(TimeEntry.corrections).selectinload(TimeEntryCorrection.segments),
        )
    )
    if exclude_entry_id is not None:
        query = query.where(TimeEntry.id != exclude_entry_id)
    for entry in db.scalars(query).all():
        for kind, existing_start, existing_end in correction_segments_for_entry(entry):
            if kind != "work":
                continue
            existing_end = existing_end or now_utc()
            if any(start < existing_end and end > existing_start for start, end in proposed_work):
                raise HTTPException(
                    status_code=409,
                    detail="Die Arbeitszeit überschneidet sich mit einer anderen Buchung dieses Mitarbeiters.",
                )


def ensure_entry_access(entry: TimeEntry, principal: AuthPrincipal) -> None:
    if entry.object.archived_at is not None or entry.object.status != "active":
        raise HTTPException(status_code=409, detail="Das zugehörige Objekt ist nicht mehr aktiv.")
    if not (
        "objects.read_all" in principal.permission_codes
        or any(assignment.user_id == principal.user.id for assignment in entry.object.assignments)
    ):
        raise HTTPException(status_code=404, detail="Arbeitszeitbuchung nicht gefunden.")


def entries_for_period(
    db: Session,
    principal: AuthPrincipal,
    *,
    from_date: date,
    to_date: date,
    employee_id: UUID | None = None,
    object_id: UUID | None = None,
    customer_id: UUID | None = None,
    entry_status: str | None = None,
):
    if to_date < from_date or (to_date - from_date).days > 366 or to_date == date.max:
        raise HTTPException(
            status_code=422,
            detail="Der Zeitraum ist ungültig oder umfasst mehr als 367 Kalendertage.",
        )
    if entry_status and entry_status not in {
        "open",
        "submitted",
        "approved",
        "rejected",
        "correction_requested",
        "locked",
    }:
        raise HTTPException(status_code=422, detail="Unbekannter Buchungsstatus.")
    zone = get_zone(get_schedule_settings(db).time_zone)
    range_start = datetime.combine(from_date, time.min, tzinfo=zone).astimezone(UTC)
    range_end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=zone).astimezone(UTC)
    query = visible_entry_query(principal).where(
        TimeEntry.started_at < range_end,
        or_(TimeEntry.ended_at.is_(None), TimeEntry.ended_at > range_start),
    )
    if employee_id:
        query = query.where(TimeEntry.employee_id == employee_id)
    if object_id:
        query = query.where(TimeEntry.object_id == object_id)
    if customer_id:
        query = query.where(SecurityObject.customer_id == customer_id)
    if entry_status:
        query = query.where(TimeEntry.status == entry_status)
    return zone.key, db.scalars(query.order_by(TimeEntry.started_at, TimeEntry.id)).unique().all()


def employee_for_start(
    db: Session,
    principal: AuthPrincipal,
    payload: TimeEntryStart,
) -> tuple[Employee, SecurityObject, ScheduleShift | None]:
    can_manage = "time_tracking.manage" in principal.permission_codes
    if can_manage and payload.employee_id is not None:
        employee = db.get(Employee, payload.employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden.")
    else:
        employee = current_employee(db, principal)
        if payload.employee_id and payload.employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Sie dürfen nur eigene Zeiten erfassen.")

    now = now_utc()
    shift = None
    if payload.shift_id:
        shift = db.scalar(select(ScheduleShift).where(ScheduleShift.id == payload.shift_id))
        if shift is None or shift.status != "published" or shift.employee_id != employee.id:
            raise HTTPException(status_code=404, detail="Veröffentlichter Dienst nicht gefunden.")
    else:
        shifts = db.scalars(
            select(ScheduleShift).where(
                ScheduleShift.employee_id == employee.id,
                ScheduleShift.status == "published",
                ScheduleShift.starts_at <= now,
                ScheduleShift.ends_at > now,
            )
        ).all()
        if len(shifts) > 1:
            raise HTTPException(status_code=409, detail="Mehrere passende Dienste gefunden.")
        shift = shifts[0] if shifts else None

    object_id = payload.object_id or (shift.object_id if shift else None)
    if shift and object_id != shift.object_id:
        raise HTTPException(status_code=409, detail="Das gewählte Objekt passt nicht zum Dienst.")
    if object_id is None:
        raise HTTPException(
            status_code=409,
            detail="Kein aktueller Dienst gefunden; eine manuelle Buchung erfordert Verwaltungsrecht.",
        )
    obj = get_object_for_user(db, object_id, principal)
    if shift is None and not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Für einen Dienst ohne Dienstplan ist eine manuelle Berechtigung erforderlich.",
        )
    require_employee_object_assignment(db, employee, obj)
    return employee, obj, shift


@router.post("/time-tracking/start", response_model=TimeEntryRead, status_code=201)
def start_time_entry(
    request: Request,
    payload: TimeEntryStart,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    if "time_tracking.create" not in principal.permission_codes and (
        "time_tracking.manage" not in principal.permission_codes
    ):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion.")
    lock_time_tracking_periods(db)
    employee, obj, shift = employee_for_start(db, principal, payload)
    lock_employee_schedule(db, employee.id)
    open_entry = db.scalar(
        select(TimeEntry.id).where(TimeEntry.employee_id == employee.id, TimeEntry.status == "open")
    )
    if open_entry:
        raise HTTPException(
            status_code=409, detail="Für diesen Mitarbeiter läuft bereits eine Buchung."
        )
    started_at = now_utc()
    entry = TimeEntry(
        employee_id=employee.id,
        object_id=obj.id,
        shift_id=shift.id if shift else None,
        started_at=started_at,
        status="open",
        created_by_id=principal.user.id,
    )
    entry.segments.append(TimeEntrySegment(position=1, kind="work", started_at=started_at))
    db.add(entry)
    flush_or_conflict(db)
    add_history(
        db,
        entry=entry,
        actor_id=principal.user.id,
        action="started",
        request=request,
        details={"employee_id": str(employee.id), "object_id": str(obj.id)},
    )
    commit_or_conflict(db)
    refreshed = get_entry(db, entry.id, principal)
    return read_entry(refreshed, get_schedule_settings(db).time_zone)


def active_segment(entry: TimeEntry, kind: str | None = None) -> TimeEntrySegment:
    active = [segment for segment in entry.segments if segment.ended_at is None]
    if len(active) != 1 or (kind and active[0].kind != kind):
        raise HTTPException(status_code=409, detail="Dieser Statuswechsel ist nicht zulässig.")
    return active[0]


@router.post("/time-tracking/entries/{entry_id}/pause", response_model=TimeEntryRead)
def pause_time_entry(
    request: Request,
    entry_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    lock_time_tracking_periods(db)
    entry = get_entry(db, entry_id, principal, for_update=True)
    if entry.status != "open":
        raise HTTPException(
            status_code=409, detail="Nur laufende Buchungen können pausiert werden."
        )
    segment = active_segment(entry, "work")
    timestamp = now_utc()
    ensure_interval_not_period_locked(
        db,
        starts_at=entry.started_at,
        ends_at=timestamp,
        time_zone=get_schedule_settings(db).time_zone,
    )
    if timestamp <= as_utc(segment.started_at):
        raise HTTPException(status_code=409, detail="Die Pause muss nach Arbeitsbeginn liegen.")
    segment.ended_at = timestamp
    entry.segments.append(
        TimeEntrySegment(
            position=max(item.position for item in entry.segments) + 1,
            kind="break",
            started_at=timestamp,
        )
    )
    add_history(
        db, entry=entry, actor_id=principal.user.id, action="break_started", request=request
    )
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.post("/time-tracking/entries/{entry_id}/resume", response_model=TimeEntryRead)
def resume_time_entry(
    request: Request,
    entry_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    lock_time_tracking_periods(db)
    entry = get_entry(db, entry_id, principal, for_update=True)
    if entry.status != "open":
        raise HTTPException(
            status_code=409, detail="Nur laufende Buchungen können fortgesetzt werden."
        )
    segment = active_segment(entry, "break")
    timestamp = now_utc()
    ensure_interval_not_period_locked(
        db,
        starts_at=entry.started_at,
        ends_at=timestamp,
        time_zone=get_schedule_settings(db).time_zone,
    )
    if timestamp <= as_utc(segment.started_at):
        raise HTTPException(status_code=409, detail="Die Pause muss vor dem Fortsetzen liegen.")
    segment.ended_at = timestamp
    entry.segments.append(
        TimeEntrySegment(
            position=max(item.position for item in entry.segments) + 1,
            kind="work",
            started_at=timestamp,
        )
    )
    add_history(db, entry=entry, actor_id=principal.user.id, action="break_ended", request=request)
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.post("/time-tracking/entries/{entry_id}/stop", response_model=TimeEntryRead)
def stop_time_entry(
    request: Request,
    entry_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    lock_time_tracking_periods(db)
    entry = get_entry(db, entry_id, principal, for_update=True)
    if entry.status != "open":
        raise HTTPException(status_code=409, detail="Nur laufende Buchungen können beendet werden.")
    timestamp = now_utc()
    ensure_interval_not_period_locked(
        db,
        starts_at=entry.started_at,
        ends_at=timestamp,
        time_zone=get_schedule_settings(db).time_zone,
    )
    segment = active_segment(entry)
    if timestamp <= as_utc(segment.started_at):
        raise HTTPException(status_code=409, detail="Das Segmentende muss nach dem Beginn liegen.")
    proposed = [
        (item.kind, as_utc(item.started_at), as_utc(item.ended_at) if item.ended_at else timestamp)
        for item in entry.segments
    ]
    lock_employee_schedule(db, entry.employee_id)
    ensure_no_work_overlap(db, entry.employee_id, proposed, exclude_entry_id=entry.id)
    segment.ended_at = timestamp
    entry.ended_at = timestamp
    entry.status = "submitted"
    entry.submitted_at = timestamp
    add_history(db, entry=entry, actor_id=principal.user.id, action="submitted", request=request)
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.post("/time-tracking/entries/manual", response_model=TimeEntryRead, status_code=201)
def create_manual_entry(
    request: Request,
    payload: TimeEntryManualCreate,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    if "time_tracking.manage" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für manuelle Buchungen.")
    lock_time_tracking_periods(db)
    employee = db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden.")
    obj = get_object_for_user(db, payload.object_id, principal)
    require_employee_object_assignment(db, employee, obj)
    starts_at, ends_at = validate_segments(payload.segments)
    ensure_interval_not_period_locked(
        db,
        starts_at=starts_at,
        ends_at=ends_at,
        time_zone=get_schedule_settings(db).time_zone,
    )
    lock_employee_schedule(db, employee.id)
    proposed = [
        (segment.kind, segment.started_at.astimezone(UTC), segment.ended_at.astimezone(UTC))
        for segment in payload.segments
    ]
    ensure_no_work_overlap(db, employee.id, proposed)
    shift = None
    if payload.shift_id:
        shift = db.scalar(select(ScheduleShift).where(ScheduleShift.id == payload.shift_id))
        if (
            shift is None
            or shift.status != "published"
            or shift.employee_id != employee.id
            or shift.object_id != obj.id
        ):
            raise HTTPException(
                status_code=422, detail="Der Dienst passt nicht zu Mitarbeiter und Objekt."
            )
    entry = TimeEntry(
        employee_id=employee.id,
        object_id=obj.id,
        shift_id=shift.id if shift else None,
        started_at=starts_at,
        ended_at=ends_at,
        status="submitted",
        created_by_id=principal.user.id,
        submitted_at=now_utc(),
    )
    entry.segments = [
        TimeEntrySegment(
            position=index,
            kind=segment.kind,
            started_at=segment.started_at.astimezone(UTC),
            ended_at=segment.ended_at.astimezone(UTC),
        )
        for index, segment in enumerate(payload.segments, start=1)
    ]
    db.add(entry)
    flush_or_conflict(db)
    add_history(
        db,
        entry=entry,
        actor_id=principal.user.id,
        action="manual_created",
        request=request,
        details={"reason": "Berechtigte manuelle Erfassung"},
    )
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.get("/time-tracking/entries", response_model=list[TimeEntryRead])
def list_time_entries(
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    from_date: date | None = None,
    to_date: date | None = None,
    employee_id: UUID | None = None,
    object_id: UUID | None = None,
    customer_id: UUID | None = None,
    entry_status: str | None = Query(default=None, alias="status"),
) -> list[TimeEntryRead]:
    permissions = principal.permission_codes
    if not ({"time_tracking.read_own", "time_tracking.read_all"} & permissions):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion.")
    if (from_date is None) != (to_date is None):
        raise HTTPException(
            status_code=422, detail="Beginn und Ende müssen gemeinsam angegeben werden."
        )
    if entry_status and entry_status not in {
        "open",
        "submitted",
        "approved",
        "rejected",
        "correction_requested",
        "locked",
    }:
        raise HTTPException(status_code=422, detail="Unbekannter Buchungsstatus.")
    zone = get_schedule_settings(db).time_zone
    if from_date is not None and to_date is not None:
        zone, entries = entries_for_period(
            db,
            principal,
            from_date=from_date,
            to_date=to_date,
            employee_id=employee_id,
            object_id=object_id,
            customer_id=customer_id,
            entry_status=entry_status,
        )
    else:
        query = visible_entry_query(principal)
        if employee_id:
            query = query.where(TimeEntry.employee_id == employee_id)
        if object_id:
            query = query.where(TimeEntry.object_id == object_id)
        if customer_id:
            query = query.where(SecurityObject.customer_id == customer_id)
        if entry_status:
            query = query.where(TimeEntry.status == entry_status)
        entries = db.scalars(query.order_by(TimeEntry.started_at.desc()).limit(500)).unique().all()
    return [read_entry(entry, zone) for entry in entries]


@router.post(
    "/time-tracking/entries/{entry_id}/corrections",
    response_model=TimeEntryCorrectionRead,
    status_code=201,
)
def request_time_correction(
    request: Request,
    entry_id: UUID,
    payload: TimeCorrectionCreate,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryCorrectionRead:
    lock_time_tracking_periods(db)
    entry = get_entry(db, entry_id, principal, for_update=True)
    is_owner = entry.employee.user_id == principal.user.id
    if is_owner:
        if "time_tracking.correct_own" not in principal.permission_codes:
            raise HTTPException(
                status_code=403, detail="Keine Berechtigung für eigene Korrekturen."
            )
    elif "time_tracking.correct_all" not in principal.permission_codes:
        raise HTTPException(status_code=404, detail="Arbeitszeitbuchung nicht gefunden.")
    ensure_entry_access(entry, principal)
    if entry.status not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=409, detail="Nur abgeschlossene Buchungen können korrigiert werden."
        )
    if any(item.status == "pending" for item in entry.corrections):
        raise HTTPException(
            status_code=409, detail="Für diese Buchung liegt bereits ein Antrag vor."
        )
    starts_at, ends_at = validate_segments(payload.segments)
    ensure_interval_not_period_locked(
        db,
        starts_at=entry.started_at,
        ends_at=entry.ended_at,
        time_zone=get_schedule_settings(db).time_zone,
    )
    ensure_interval_not_period_locked(
        db,
        starts_at=starts_at,
        ends_at=ends_at,
        time_zone=get_schedule_settings(db).time_zone,
    )
    correction = TimeEntryCorrection(
        entry=entry,
        requested_by_id=principal.user.id,
        reason=payload.reason,
        previous_status=entry.status,
    )
    correction.segments = [
        TimeEntryCorrectionSegment(
            position=index,
            kind=segment.kind,
            started_at=segment.started_at.astimezone(UTC),
            ended_at=segment.ended_at.astimezone(UTC),
        )
        for index, segment in enumerate(payload.segments, start=1)
    ]
    db.add(correction)
    entry.status = "correction_requested"
    entry.updated_at = now_utc()
    flush_or_conflict(db)
    add_history(
        db,
        entry=entry,
        actor_id=principal.user.id,
        action="correction_requested",
        request=request,
        details={
            "correction_id": str(correction.id),
            "reason": payload.reason,
            "proposed_start": starts_at.isoformat(),
            "proposed_end": ends_at.isoformat(),
        },
    )
    commit_or_conflict(db)
    return read_correction(correction)


def get_correction(
    db: Session,
    correction_id: UUID,
    principal: AuthPrincipal,
    *,
    for_update: bool = False,
) -> TimeEntryCorrection:
    query = (
        select(TimeEntryCorrection)
        .options(
            joinedload(TimeEntryCorrection.entry).joinedload(TimeEntry.employee),
            joinedload(TimeEntryCorrection.entry)
            .joinedload(TimeEntry.object)
            .joinedload(SecurityObject.customer),
            joinedload(TimeEntryCorrection.entry).selectinload(TimeEntry.corrections),
            selectinload(TimeEntryCorrection.segments),
        )
        .join(TimeEntry)
        .where(TimeEntryCorrection.id == correction_id)
    )
    if for_update:
        query = query.with_for_update(of=TimeEntryCorrection)
    correction = db.scalar(query)
    if correction is None:
        raise HTTPException(status_code=404, detail="Korrekturantrag nicht gefunden.")
    ensure_entry_access(correction.entry, principal)
    if "time_tracking.read_all" not in principal.permission_codes and (
        correction.entry.employee.user_id != principal.user.id
    ):
        raise HTTPException(status_code=404, detail="Korrekturantrag nicht gefunden.")
    return correction


@router.get("/time-tracking/corrections", response_model=list[TimeEntryCorrectionRead])
def list_time_corrections(
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    pending_only: bool = True,
) -> list[TimeEntryCorrectionRead]:
    if "time_tracking.read_all" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion.")
    query = (
        select(TimeEntryCorrection)
        .join(TimeEntry)
        .options(selectinload(TimeEntryCorrection.segments))
        .order_by(TimeEntryCorrection.requested_at.desc())
        .limit(500)
    )
    if pending_only:
        query = query.where(TimeEntryCorrection.status == "pending")
    corrections = db.scalars(query).all()
    visible = []
    for correction in corrections:
        try:
            ensure_entry_access(get_entry(db, correction.entry_id, principal), principal)
        except HTTPException as exc:
            if exc.status_code in {403, 404}:
                continue
            raise
        visible.append(read_correction(correction))
    return visible


def ensure_not_self_approval(entry: TimeEntry, principal: AuthPrincipal) -> None:
    if entry.employee.user_id == principal.user.id:
        raise HTTPException(
            status_code=403, detail="Eigene Arbeitszeiten dürfen nicht freigegeben werden."
        )


@router.post("/time-tracking/entries/{entry_id}/approve", response_model=TimeEntryRead)
def approve_time_entry(
    request: Request,
    entry_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    if "time_tracking.approve" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Freigaben.")
    lock_time_tracking_periods(db)
    entry = get_entry(db, entry_id, principal, for_update=True)
    ensure_not_self_approval(entry, principal)
    ensure_entry_access(entry, principal)
    if entry.status != "submitted":
        raise HTTPException(
            status_code=409, detail="Nur eingereichte Buchungen können freigegeben werden."
        )
    timestamp = now_utc()
    entry.status = "approved"
    entry.reviewed_by_id = principal.user.id
    entry.reviewed_at = timestamp
    entry.decision_reason = None
    add_history(db, entry=entry, actor_id=principal.user.id, action="approved", request=request)
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.post("/time-tracking/entries/{entry_id}/reject", response_model=TimeEntryRead)
def reject_time_entry(
    request: Request,
    entry_id: UUID,
    payload: TimeEntryDecision,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    if "time_tracking.reject" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Ablehnungen.")
    if not payload.reason:
        raise HTTPException(status_code=422, detail="Eine Ablehnungsbegründung ist erforderlich.")
    lock_time_tracking_periods(db)
    entry = get_entry(db, entry_id, principal, for_update=True)
    ensure_not_self_approval(entry, principal)
    ensure_entry_access(entry, principal)
    if entry.status != "submitted":
        raise HTTPException(
            status_code=409, detail="Nur eingereichte Buchungen können abgelehnt werden."
        )
    entry.status = "rejected"
    entry.reviewed_by_id = principal.user.id
    entry.reviewed_at = now_utc()
    entry.decision_reason = payload.reason
    add_history(
        db,
        entry=entry,
        actor_id=principal.user.id,
        action="rejected",
        request=request,
        details={"reason": payload.reason},
    )
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.post(
    "/time-tracking/corrections/{correction_id}/approve",
    response_model=TimeEntryRead,
)
def approve_time_correction(
    request: Request,
    correction_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    if "time_tracking.approve" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Freigaben.")
    lock_time_tracking_periods(db)
    correction = get_correction(db, correction_id, principal, for_update=True)
    entry = get_entry(db, correction.entry_id, principal, for_update=True)
    ensure_not_self_approval(entry, principal)
    if correction.status != "pending" or entry.status != "correction_requested":
        raise HTTPException(status_code=409, detail="Dieser Korrekturantrag ist nicht mehr offen.")
    proposed = [
        (segment.kind, as_utc(segment.started_at), as_utc(segment.ended_at))
        for segment in correction.segments
    ]
    ensure_interval_not_period_locked(
        db,
        starts_at=entry.started_at,
        ends_at=entry.ended_at,
        time_zone=get_schedule_settings(db).time_zone,
    )
    ensure_interval_not_period_locked(
        db,
        starts_at=proposed[0][1],
        ends_at=proposed[-1][2],
        time_zone=get_schedule_settings(db).time_zone,
    )
    lock_employee_schedule(db, entry.employee_id)
    ensure_no_work_overlap(db, entry.employee_id, proposed, exclude_entry_id=entry.id)
    timestamp = now_utc()
    correction.status = "approved"
    correction.decided_by_id = principal.user.id
    correction.decided_at = timestamp
    entry.status = "approved"
    entry.started_at = proposed[0][1]
    entry.ended_at = proposed[-1][2]
    entry.updated_at = timestamp
    entry.reviewed_by_id = principal.user.id
    entry.reviewed_at = timestamp
    entry.decision_reason = None
    add_history(
        db,
        entry=entry,
        actor_id=principal.user.id,
        action="correction_approved",
        request=request,
        details={"correction_id": str(correction.id)},
    )
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.post(
    "/time-tracking/corrections/{correction_id}/reject",
    response_model=TimeEntryRead,
)
def reject_time_correction(
    request: Request,
    correction_id: UUID,
    payload: TimeEntryDecision,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    if "time_tracking.reject" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Ablehnungen.")
    if not payload.reason:
        raise HTTPException(status_code=422, detail="Eine Ablehnungsbegründung ist erforderlich.")
    lock_time_tracking_periods(db)
    correction = get_correction(db, correction_id, principal, for_update=True)
    entry = get_entry(db, correction.entry_id, principal, for_update=True)
    ensure_not_self_approval(entry, principal)
    if correction.status != "pending" or entry.status != "correction_requested":
        raise HTTPException(status_code=409, detail="Dieser Korrekturantrag ist nicht mehr offen.")
    correction.status = "rejected"
    correction.rejection_reason = payload.reason
    correction.decided_by_id = principal.user.id
    correction.decided_at = now_utc()
    entry.status = correction.previous_status
    entry.reviewed_by_id = principal.user.id
    entry.reviewed_at = correction.decided_at
    entry.decision_reason = payload.reason
    add_history(
        db,
        entry=entry,
        actor_id=principal.user.id,
        action="correction_rejected",
        request=request,
        details={"correction_id": str(correction.id), "reason": payload.reason},
    )
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.post("/time-tracking/entries/{entry_id}/lock", response_model=TimeEntryRead)
def lock_time_entry(
    request: Request,
    entry_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
) -> TimeEntryRead:
    if "time_tracking.manage" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung zum Sperren von Buchungen.")
    lock_time_tracking_periods(db)
    entry = get_entry(db, entry_id, principal, for_update=True)
    ensure_interval_not_period_locked(
        db,
        starts_at=entry.started_at,
        ends_at=entry.ended_at,
        time_zone=get_schedule_settings(db).time_zone,
    )
    if entry.status != "approved":
        raise HTTPException(
            status_code=409, detail="Nur freigegebene Buchungen können gesperrt werden."
        )
    entry.status = "locked"
    add_history(db, entry=entry, actor_id=principal.user.id, action="locked", request=request)
    commit_or_conflict(db)
    return read_entry(get_entry(db, entry.id, principal), get_schedule_settings(db).time_zone)


@router.get("/time-tracking/reports", response_model=TimeEntrySummaryRead)
def get_time_report(
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    from_date: date,
    to_date: date,
    employee_id: UUID | None = None,
    object_id: UUID | None = None,
    customer_id: UUID | None = None,
    entry_status: str | None = Query(default=None, alias="status"),
    group_by: str | None = None,
) -> TimeEntrySummaryRead:
    if not ({"time_tracking.read_own", "time_tracking.read_all"} & principal.permission_codes):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Auswertungen.")
    zone, entries = entries_for_period(
        db,
        principal,
        from_date=from_date,
        to_date=to_date,
        employee_id=employee_id,
        object_id=object_id,
        customer_id=customer_id,
        entry_status=entry_status,
    )
    rows = [read_entry(entry, zone) for entry in entries]
    allowed_groups = {"employee", "object", "customer", "day", "week", "month"}
    if group_by is not None and group_by not in allowed_groups:
        raise HTTPException(status_code=422, detail="Ungültige Gruppierung.")
    grouped: dict[str, dict[str, object]] = {}
    if group_by:
        for item, entry in zip(rows, entries, strict=True):
            local_day = item.started_at.astimezone(get_zone(zone)).date()
            if group_by == "employee":
                key, label = str(item.employee_id), item.employee_name
            elif group_by == "object":
                key, label = str(item.object_id), item.object_name
            elif group_by == "customer":
                key, label = str(item.customer_id), item.customer_name
            elif group_by == "day":
                key = label = local_day.isoformat()
            elif group_by == "week":
                iso_week = local_day.isocalendar()
                key = f"{iso_week.year}-W{iso_week.week:02d}"
                label = f"Kalenderwoche {iso_week.week}, {iso_week.year}"
            else:
                key = label = local_day.strftime("%Y-%m")
            group = grouped.setdefault(
                key,
                {
                    "key": key,
                    "label": label,
                    "entry_count": 0,
                    "actual_work_seconds": 0.0,
                    "actual_break_seconds": 0.0,
                    "planned_work_seconds": 0,
                    "difference_seconds": 0.0,
                    "overtime_seconds": 0.0,
                    "pending_count": 0,
                },
            )
            group["entry_count"] += 1
            group["actual_work_seconds"] += item.actual_work_seconds
            group["actual_break_seconds"] += item.actual_break_seconds
            group["planned_work_seconds"] += item.planned_work_seconds or 0
            group["difference_seconds"] += item.difference_seconds or 0
            group["overtime_seconds"] += max(0, item.difference_seconds or 0)
            group["pending_count"] += item.status in {"submitted", "correction_requested"}
    return TimeEntrySummaryRead(
        from_date=from_date,
        to_date=to_date,
        time_zone=zone,
        group_by=group_by,
        entry_count=len(rows),
        actual_work_seconds=sum(row.actual_work_seconds for row in rows),
        actual_break_seconds=sum(row.actual_break_seconds for row in rows),
        planned_work_seconds=sum(row.planned_work_seconds or 0 for row in rows),
        difference_seconds=sum(row.difference_seconds or 0 for row in rows),
        overtime_seconds=sum(max(0, row.difference_seconds or 0) for row in rows),
        pending_count=sum(row.status in {"submitted", "correction_requested"} for row in rows),
        groups=[TimeEntryReportGroup(**item) for item in grouped.values()],
        items=rows,
    )


@router.get("/time-tracking/reports/missing", response_model=list[MissingShiftRead])
def get_missing_shift_times(
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    from_date: date,
    to_date: date,
) -> list[MissingShiftRead]:
    if "time_tracking.read_all" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Auswertung.")
    zone = get_zone(get_schedule_settings(db).time_zone)
    if to_date < from_date or (to_date - from_date).days > 366 or to_date == date.max:
        raise HTTPException(status_code=422, detail="Der Zeitraum ist ungültig.")
    start = datetime.combine(from_date, time.min, tzinfo=zone).astimezone(UTC)
    end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=zone).astimezone(UTC)
    query = (
        select(ScheduleShift)
        .join(Employee, ScheduleShift.employee_id == Employee.id)
        .join(SecurityObject, ScheduleShift.object_id == SecurityObject.id)
        .options(joinedload(ScheduleShift.employee), joinedload(ScheduleShift.object))
        .where(
            ScheduleShift.status == "published",
            ScheduleShift.starts_at < end,
            ScheduleShift.ends_at > start,
            ~select(TimeEntry.id).where(TimeEntry.shift_id == ScheduleShift.id).exists(),
        )
        .order_by(ScheduleShift.starts_at)
    )
    if "objects.read_all" not in principal.permission_codes:
        query = query.where(
            SecurityObject.assignments.any(ObjectAssignment.user_id == principal.user.id)
        )
    return [
        MissingShiftRead(
            shift_id=shift.id,
            employee_id=shift.employee_id,
            employee_number=shift.employee.employee_number,
            employee_name=shift.employee.full_name,
            object_id=shift.object_id,
            object_code=shift.object.code,
            object_name=shift.object.name,
            starts_at=as_utc(shift.starts_at),
            ends_at=as_utc(shift.ends_at),
            time_zone=zone.key,
        )
        for shift in db.scalars(query).all()
    ]


def safe_csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


@router.get("/time-tracking/export.csv")
def export_time_entries(
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(get_auth_principal)],
    from_date: date,
    to_date: date,
    employee_id: UUID | None = None,
    object_id: UUID | None = None,
    customer_id: UUID | None = None,
) -> Response:
    if "time_tracking.export" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für den CSV-Export.")
    zone, entries = entries_for_period(
        db,
        principal,
        from_date=from_date,
        to_date=to_date,
        employee_id=employee_id,
        object_id=object_id,
        customer_id=customer_id,
    )
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(
        [
            "Mitarbeiter-Nr.",
            "Mitarbeiter",
            "Kunde",
            "Objekt",
            "Dienstbeginn",
            "Dienstende",
            "Sollzeit (Sekunden)",
            "Istzeit (Sekunden)",
            "Pause (Sekunden)",
            "Abweichung (Sekunden)",
            "Status",
        ]
    )
    for entry in entries:
        row = read_entry(entry, zone)
        if row.status not in {"approved", "locked"}:
            continue
        values = [
            entry.employee.employee_number,
            entry.employee.full_name,
            entry.object.customer.company_name,
            entry.object.name,
            row.started_at.astimezone(get_zone(zone)).isoformat(),
            row.ended_at.astimezone(get_zone(zone)).isoformat() if row.ended_at else "",
            row.planned_work_seconds,
            row.actual_work_seconds,
            row.actual_break_seconds,
            row.difference_seconds,
            row.status,
        ]
        writer.writerow([safe_csv_cell(value) for value in values])
    content = "\ufeff" + buffer.getvalue()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="arbeitszeiten.csv"'},
    )
