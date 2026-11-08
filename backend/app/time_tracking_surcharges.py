import csv
import hashlib
import io
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

import holidays
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth import AuthPrincipal, add_audit_entry, require_permission
from app.database import get_db
from app.models import (
    Employee,
    ObjectAssignment,
    ScheduleShift,
    SecurityObject,
    TimeEntry,
    TimeEntryCorrection,
    TimeSurchargeCalculation,
    TimeSurchargeRule,
    TimeTrackingPeriod,
    TimeTrackingSettings,
)
from app.scheduling_api import as_utc, get_schedule_settings, get_zone
from app.schemas import (
    TimeSurchargeCalculationRead,
    TimeSurchargeRuleCreate,
    TimeSurchargeRuleRead,
    TimeTrackingPeriodLockCreate,
    TimeTrackingPeriodRead,
    TimeTrackingSettingsRead,
    TimeTrackingSettingsUpdate,
)

router = APIRouter()

PERIOD_LOCK_ADVISORY_KEY = int.from_bytes(
    hashlib.sha256(b"securityops:time-tracking-periods").digest()[:8],
    byteorder="big",
    signed=True,
)
MICROSECONDS_PER_SECOND = Decimal(1_000_000)


def get_time_tracking_settings(db: Session) -> TimeTrackingSettings:
    settings = db.get(TimeTrackingSettings, 1)
    if settings is None:
        settings = TimeTrackingSettings(id=1, federal_state=None)
        db.add(settings)
        db.flush()
    return settings


def lock_time_tracking_periods(db: Session) -> None:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(select(func.pg_advisory_xact_lock(PERIOD_LOCK_ADVISORY_KEY)))


def local_period_bounds(
    from_date: date, to_date: date, zone: ZoneInfo
) -> tuple[datetime, datetime]:
    start = datetime.combine(from_date, time.min, tzinfo=zone).astimezone(UTC)
    end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=zone).astimezone(UTC)
    return start, end


def ensure_interval_not_period_locked(
    db: Session,
    *,
    starts_at: datetime,
    ends_at: datetime | None,
    time_zone: str,
) -> None:
    get_zone(time_zone)
    start = as_utc(starts_at)
    end = as_utc(ends_at) if ends_at is not None else datetime.now(UTC)
    if end <= start:
        return
    for period in db.scalars(select(TimeTrackingPeriod)).all():
        period_start, period_end = local_period_bounds(
            period.from_date, period.to_date, get_zone(period.time_zone)
        )
        if start < period_end and end > period_start:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Die Arbeitszeit liegt in einer gesperrten Abrechnungsperiode.",
            )


def _rule_snapshot(rule: TimeSurchargeRule) -> dict[str, object]:
    return {
        "id": str(rule.id),
        "code": rule.code,
        "name": rule.name,
        "category": rule.category,
        "calculation_type": rule.calculation_type,
        "configured_value": str(rule.value),
        "currency": rule.currency,
        "basis_description": rule.basis_description,
        "valid_from": rule.valid_from.isoformat(),
        "valid_to": rule.valid_to.isoformat() if rule.valid_to else None,
        "priority": rule.priority,
        "combination_mode": rule.combination_mode,
        "weekdays": rule.weekdays,
        "starts_local": rule.starts_local,
        "ends_local": rule.ends_local,
    }


def _seconds(duration: timedelta) -> Decimal:
    return (
        Decimal(duration.days * 86400 + duration.seconds)
        + Decimal(duration.microseconds) / MICROSECONDS_PER_SECOND
    )


def _local_boundary(day: date, value: str, zone: ZoneInfo) -> set[datetime]:
    hour, minute = (int(part) for part in value.split(":"))
    local = datetime.combine(day, time(hour, minute))
    result = set()
    for fold in (0, 1):
        candidate = local.replace(tzinfo=zone, fold=fold)
        utc_value = candidate.astimezone(UTC)
        if utc_value.astimezone(zone).replace(tzinfo=None) == local:
            result.add(utc_value)
    return result


def _dst_transitions(start: datetime, end: datetime, zone: ZoneInfo) -> set[datetime]:
    boundaries: set[datetime] = set()
    cursor = start
    previous_offset = cursor.astimezone(zone).utcoffset()
    step = timedelta(hours=6)
    while cursor < end:
        next_cursor = min(cursor + step, end)
        next_offset = next_cursor.astimezone(zone).utcoffset()
        if next_offset != previous_offset:
            low = int(cursor.timestamp())
            high = int(next_cursor.timestamp())
            while high - low > 1:
                middle = (low + high) // 2
                if (
                    datetime.fromtimestamp(middle, UTC).astimezone(zone).utcoffset()
                    == previous_offset
                ):
                    low = middle
                else:
                    high = middle
            boundaries.add(datetime.fromtimestamp(high, UTC))
        cursor = next_cursor
        previous_offset = next_offset
    return boundaries


def _rule_window_applies(rule: TimeSurchargeRule, local: datetime) -> bool:
    weekday = local.weekday()
    if rule.category == "saturday":
        return weekday == 5
    if rule.category == "sunday":
        return weekday == 6
    if rule.category in {"public_holiday"}:
        return False
    if rule.category == "night":
        assert rule.starts_local is not None and rule.ends_local is not None
        start_time = time.fromisoformat(rule.starts_local)
        end_time = time.fromisoformat(rule.ends_local)
        return (
            start_time <= local.time().replace(tzinfo=None) < end_time
            if start_time < end_time
            else local.time().replace(tzinfo=None) >= start_time
            or local.time().replace(tzinfo=None) < end_time
        )
    assert rule.starts_local is not None and rule.ends_local is not None
    if not rule.weekdays:
        return False
    start_time = time.fromisoformat(rule.starts_local)
    end_time = time.fromisoformat(rule.ends_local)
    local_time = local.time().replace(tzinfo=None)
    if start_time < end_time:
        return weekday in rule.weekdays and start_time <= local_time < end_time
    if local_time >= start_time:
        return weekday in rule.weekdays
    previous_weekday = (weekday - 1) % 7
    return local_time < end_time and previous_weekday in rule.weekdays


def _matched_rules(
    instant: datetime,
    *,
    rules: list[TimeSurchargeRule],
    zone: ZoneInfo,
    holiday_dates: set[date],
) -> list[TimeSurchargeRule]:
    local = instant.astimezone(zone)
    matches = []
    for rule in rules:
        if local.date() < rule.valid_from or (rule.valid_to and local.date() > rule.valid_to):
            continue
        if rule.category == "public_holiday":
            applies = local.date() in holiday_dates
        else:
            applies = _rule_window_applies(rule, local)
        if applies:
            matches.append(rule)
    if not matches:
        return []
    highest_priority = max(rule.priority for rule in matches)
    top = [rule for rule in matches if rule.priority == highest_priority]
    if len(top) > 1 and any(rule.combination_mode != "combine" for rule in top):
        raise HTTPException(
            status_code=409,
            detail="Mehrere gleich priorisierte Zuschlagsregeln überschneiden sich.",
        )
    if all(rule.combination_mode == "combine" for rule in top):
        return sorted(
            [rule for rule in matches if rule.combination_mode == "combine"],
            key=lambda rule: (-rule.priority, rule.code, str(rule.id)),
        )
    return top


def _entry_segments(entry: TimeEntry) -> list[tuple[str, datetime, datetime]]:
    approved = sorted(
        (correction for correction in entry.corrections if correction.status == "approved"),
        key=lambda correction: (
            as_utc(correction.decided_at)
            if correction.decided_at
            else datetime.min.replace(tzinfo=UTC),
            str(correction.id),
        ),
    )
    source_segments = approved[-1].segments if approved else entry.segments
    return [
        (segment.kind, as_utc(segment.started_at), as_utc(segment.ended_at))
        for segment in source_segments
        if segment.kind == "work" and segment.ended_at is not None
    ]


def calculate_snapshot(
    db: Session,
    *,
    entry: TimeEntry,
    actor_id: UUID,
    permit_locked_period: bool = False,
) -> TimeSurchargeCalculation:
    if entry.status not in {"approved", "locked"}:
        raise HTTPException(
            status_code=409,
            detail="Zuschläge können nur für freigegebene oder gesperrte Buchungen berechnet werden.",
        )
    schedule_settings = get_schedule_settings(db)
    tracking_settings = get_time_tracking_settings(db)
    zone = get_zone(schedule_settings.time_zone)
    segments = _entry_segments(entry)
    if not segments:
        raise HTTPException(
            status_code=409, detail="Die Buchung enthält keine abgeschlossene Arbeit."
        )
    if not permit_locked_period:
        for segment_start, segment_end in ((start, end) for _, start, end in segments):
            ensure_interval_not_period_locked(
                db,
                starts_at=segment_start,
                ends_at=segment_end,
                time_zone=schedule_settings.time_zone,
            )
    rules = db.scalars(
        select(TimeSurchargeRule).order_by(
            TimeSurchargeRule.priority.desc(), TimeSurchargeRule.code, TimeSurchargeRule.id
        )
    ).all()

    holiday_rules_exist = any(rule.category == "public_holiday" for rule in rules)
    if holiday_rules_exist and tracking_settings.federal_state is None:
        raise HTTPException(
            status_code=409,
            detail="Für Feiertagszuschläge muss zuerst ein Bundesland konfiguriert werden.",
        )
    holiday_dates: set[date] = set()
    if tracking_settings.federal_state:
        years = {
            year
            for _, start, end in segments
            for year in range(
                (start.astimezone(zone).date() - timedelta(days=1)).year,
                (end.astimezone(zone).date() + timedelta(days=1)).year + 1,
            )
        }
        holiday_calendar = holidays.country_holidays(
            "DE",
            subdiv=tracking_settings.federal_state,
            years=years,
            observed=False,
        )
        holiday_dates = set(holiday_calendar.keys())

    allocations: dict[UUID, Decimal] = {}
    unallocated = Decimal(0)
    gross = Decimal(0)
    for _, start, end in segments:
        gross += _seconds(end - start)
        boundaries = {start, end}
        boundaries.update(_dst_transitions(start, end, zone))
        first_local_day = start.astimezone(zone).date() - timedelta(days=1)
        last_local_day = end.astimezone(zone).date() + timedelta(days=1)
        current_day = first_local_day
        while current_day <= last_local_day:
            boundaries.update(_local_boundary(current_day, "00:00", zone))
            for rule in rules:
                if rule.starts_local:
                    boundaries.update(_local_boundary(current_day, rule.starts_local, zone))
                if rule.ends_local:
                    boundaries.update(_local_boundary(current_day, rule.ends_local, zone))
            current_day += timedelta(days=1)
        ordered = sorted(value for value in boundaries if start <= value <= end)
        for interval_start, interval_end in pairwise(ordered):
            if interval_start >= interval_end:
                continue
            midpoint = interval_start + (interval_end - interval_start) / 2
            seconds = _seconds(interval_end - interval_start)
            matching = _matched_rules(
                midpoint,
                rules=rules,
                zone=zone,
                holiday_dates=holiday_dates,
            )
            if not matching:
                unallocated += seconds
            for rule in matching:
                allocations[rule.id] = allocations.get(rule.id, Decimal(0)) + seconds

    rule_by_id = {rule.id: rule for rule in rules}
    allocation_snapshot: list[dict[str, object]] = []
    for rule_id, seconds in sorted(
        allocations.items(),
        key=lambda item: (-rule_by_id[item[0]].priority, rule_by_id[item[0]].code),
    ):
        rule = rule_by_id[rule_id]
        allocation_snapshot.append(
            {
                "rule_id": str(rule.id),
                "rule_code": rule.code,
                "rule_name": rule.name,
                "eligible_work_seconds": str(seconds),
                "configured_value": str(rule.value),
                "calculation_type": rule.calculation_type,
                "currency": rule.currency,
                "basis_description": rule.basis_description,
                "calculated_amount": None,
                "calculation_note": (
                    "Kein Geldbetrag berechnet: Lohnbasis, Zuschlagseinheit und Rundungsregel "
                    "sind nicht als Abrechnungskonvention festgelegt."
                ),
            }
        )
    if unallocated:
        allocation_snapshot.append(
            {
                "rule_id": None,
                "rule_code": None,
                "rule_name": "Kein Zuschlag konfiguriert",
                "eligible_work_seconds": str(unallocated),
                "configured_value": None,
                "calculation_type": None,
                "currency": None,
                "basis_description": None,
                "calculated_amount": None,
                "calculation_note": "Tatsächlich geleistete Arbeit ohne passende Zuschlagsregel.",
            }
        )

    previous_version = db.scalar(
        select(func.max(TimeSurchargeCalculation.version)).where(
            TimeSurchargeCalculation.entry_id == entry.id
        )
    )
    return TimeSurchargeCalculation(
        entry_id=entry.id,
        version=(previous_version or 0) + 1,
        gross_work_seconds=str(gross),
        time_zone=schedule_settings.time_zone,
        federal_state=tracking_settings.federal_state,
        rule_snapshot=[_rule_snapshot(rule) for rule in rules],
        allocation_snapshot=allocation_snapshot,
        source_segments=[
            {
                "kind": kind,
                "started_at": start.isoformat(),
                "ended_at": end.isoformat(),
            }
            for kind, start, end in segments
        ],
        created_by_id=actor_id,
    )


def _read_period(period: TimeTrackingPeriod) -> TimeTrackingPeriodRead:
    return TimeTrackingPeriodRead(
        id=period.id,
        from_date=period.from_date,
        to_date=period.to_date,
        time_zone=period.time_zone,
        federal_state=period.federal_state,
        locked_by_id=period.locked_by_id,
        locked_at=as_utc(period.locked_at),
    )


def _visible_entry_query(principal: AuthPrincipal):
    query = (
        select(TimeEntry)
        .join(Employee, TimeEntry.employee_id == Employee.id)
        .join(SecurityObject, TimeEntry.object_id == SecurityObject.id)
        .options(
            joinedload(TimeEntry.employee),
            joinedload(TimeEntry.object),
            selectinload(TimeEntry.segments),
            selectinload(TimeEntry.corrections).selectinload(TimeEntryCorrection.segments),
        )
    )
    if "time_tracking.read_all" not in principal.permission_codes:
        query = query.where(Employee.user_id == principal.user.id)
    if "objects.read_all" not in principal.permission_codes:
        query = query.where(
            SecurityObject.assignments.any(ObjectAssignment.user_id == principal.user.id)
        )
    return query


def _get_calculation_entry(db: Session, entry_id: UUID, principal: AuthPrincipal) -> TimeEntry:
    entry = db.scalar(_visible_entry_query(principal).where(TimeEntry.id == entry_id))
    if entry is None:
        raise HTTPException(status_code=404, detail="Arbeitszeitbuchung nicht gefunden.")
    if entry.object.archived_at is not None or entry.object.status != "active":
        raise HTTPException(status_code=409, detail="Das zugehörige Objekt ist nicht mehr aktiv.")
    return entry


def _latest_surcharge_calculation_query(
    *,
    principal: AuthPrincipal,
    start: datetime,
    end: datetime,
):
    latest_version = (
        select(func.max(TimeSurchargeCalculation.version))
        .where(TimeSurchargeCalculation.entry_id == TimeEntry.id)
        .correlate(TimeEntry)
        .scalar_subquery()
    )
    query = (
        select(TimeSurchargeCalculation, TimeEntry)
        .join(TimeEntry, TimeEntry.id == TimeSurchargeCalculation.entry_id)
        .join(Employee, TimeEntry.employee_id == Employee.id)
        .join(SecurityObject, TimeEntry.object_id == SecurityObject.id)
        .where(
            TimeEntry.started_at < end,
            or_(TimeEntry.ended_at.is_(None), TimeEntry.ended_at > start),
            TimeSurchargeCalculation.version == latest_version,
        )
    )
    if "time_tracking.read_all" not in principal.permission_codes:
        query = query.where(Employee.user_id == principal.user.id)
    if "objects.read_all" not in principal.permission_codes:
        query = query.where(
            SecurityObject.assignments.any(ObjectAssignment.user_id == principal.user.id)
        )
    return query.order_by(TimeEntry.started_at, TimeSurchargeCalculation.entry_id)


def _safe_csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def _current_source_segments(entry: TimeEntry) -> list[dict[str, str]]:
    return [
        {
            "kind": kind,
            "started_at": start.isoformat(),
            "ended_at": end.isoformat(),
        }
        for kind, start, end in _entry_segments(entry)
    ]


@router.get(
    "/time-tracking/reports/surcharges",
    response_model=list[TimeSurchargeCalculationRead],
)
def report_time_surcharge_calculations(
    from_date: date,
    to_date: date,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[
        AuthPrincipal, Depends(require_permission("time_tracking.surcharges.read"))
    ],
) -> list[TimeSurchargeCalculationRead]:
    if "time_tracking.read_all" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Auswertung.")
    if to_date < from_date or (to_date - from_date).days > 366 or to_date == date.max:
        raise HTTPException(status_code=422, detail="Der Zeitraum ist ungültig.")
    zone = get_zone(get_schedule_settings(db).time_zone)
    start, end = local_period_bounds(from_date, to_date, zone)
    rows = db.execute(
        _latest_surcharge_calculation_query(principal=principal, start=start, end=end)
    ).all()
    return [
        calculation
        for calculation, entry in rows
        if calculation.source_segments == _current_source_segments(entry)
    ]


@router.get("/time-tracking/export-surcharges.csv")
def export_time_surcharge_calculations(
    from_date: date,
    to_date: date,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(require_permission("time_tracking.export"))],
) -> Response:
    if "time_tracking.surcharges.read" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Zuschlagsberichte.")
    if to_date < from_date or (to_date - from_date).days > 366 or to_date == date.max:
        raise HTTPException(status_code=422, detail="Der Zeitraum ist ungültig.")
    zone = get_zone(get_schedule_settings(db).time_zone)
    start, end = local_period_bounds(from_date, to_date, zone)
    rows = db.execute(
        _latest_surcharge_calculation_query(principal=principal, start=start, end=end)
    ).all()
    calculations = [
        calculation
        for calculation, entry in rows
        if calculation.source_segments == _current_source_segments(entry)
    ]
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(
        [
            "Buchung",
            "Berechnungsversion",
            "Erstellt am (UTC)",
            "Zeitzone",
            "Bundesland",
            "Regelcode",
            "Zuschlagsart",
            "Berechnungsart",
            "Konfigurierter Wert",
            "Währung",
            "Bezugsbeschreibung",
            "Zuschlagsfähige Arbeitszeit (Sekunden)",
            "Berechneter Geldbetrag",
            "Hinweis",
        ]
    )
    for calculation in calculations:
        for allocation in calculation.allocation_snapshot:
            writer.writerow(
                [
                    _safe_csv_cell(value)
                    for value in [
                        calculation.entry_id,
                        calculation.version,
                        as_utc(calculation.created_at).isoformat(),
                        calculation.time_zone,
                        calculation.federal_state,
                        allocation.get("rule_code"),
                        allocation.get("rule_name"),
                        allocation.get("calculation_type"),
                        allocation.get("configured_value"),
                        allocation.get("currency"),
                        allocation.get("basis_description"),
                        allocation.get("eligible_work_seconds"),
                        allocation.get("calculated_amount"),
                        allocation.get("calculation_note"),
                    ]
                ]
            )
    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="zuschlagsnachweise.csv"'},
    )


@router.get("/time-tracking/settings", response_model=TimeTrackingSettingsRead)
def read_time_tracking_settings(
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[
        AuthPrincipal, Depends(require_permission("time_tracking.surcharges.read"))
    ],
) -> TimeTrackingSettingsRead:
    settings = get_time_tracking_settings(db)
    return TimeTrackingSettingsRead(
        federal_state=settings.federal_state,
        updated_at=as_utc(settings.updated_at),
    )


@router.patch("/time-tracking/settings", response_model=TimeTrackingSettingsRead)
def update_time_tracking_settings(
    request: Request,
    payload: TimeTrackingSettingsUpdate,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[
        AuthPrincipal, Depends(require_permission("time_tracking.surcharges.manage"))
    ],
) -> TimeTrackingSettingsRead:
    lock_time_tracking_periods(db)
    settings = db.scalar(
        select(TimeTrackingSettings).where(TimeTrackingSettings.id == 1).with_for_update()
    )
    if settings is None:
        settings = get_time_tracking_settings(db)
    if settings.federal_state != payload.federal_state:
        settings.federal_state = payload.federal_state
        settings.updated_by_id = principal.user.id
        add_audit_entry(
            db,
            actor_id=principal.user.id,
            action="time_tracking.settings_updated",
            entity_type="time_tracking_settings",
            entity_id="1",
            ip_address=request.client.host if request.client else None,
            details={"fields": ["federal_state"]},
        )
        db.commit()
        db.refresh(settings)
    return TimeTrackingSettingsRead(
        federal_state=settings.federal_state,
        updated_at=as_utc(settings.updated_at),
    )


@router.get("/time-tracking/surcharge-rules", response_model=list[TimeSurchargeRuleRead])
def list_time_surcharge_rules(
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[
        AuthPrincipal, Depends(require_permission("time_tracking.surcharges.read"))
    ],
) -> list[TimeSurchargeRuleRead]:
    return db.scalars(
        select(TimeSurchargeRule).order_by(
            TimeSurchargeRule.priority.desc(), TimeSurchargeRule.code
        )
    ).all()


@router.post(
    "/time-tracking/surcharge-rules",
    response_model=TimeSurchargeRuleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_time_surcharge_rule(
    request: Request,
    payload: TimeSurchargeRuleCreate,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[
        AuthPrincipal, Depends(require_permission("time_tracking.surcharges.manage"))
    ],
) -> TimeSurchargeRuleRead:
    lock_time_tracking_periods(db)
    if (
        payload.category == "public_holiday"
        and get_time_tracking_settings(db).federal_state is None
    ):
        raise HTTPException(
            status_code=409,
            detail="Vor einer Feiertagsregel muss ein Bundesland konfiguriert werden.",
        )
    rule = TimeSurchargeRule(
        **payload.model_dump(),
        created_by_id=principal.user.id,
    )
    db.add(rule)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Der Regelcode ist bereits vergeben.") from exc
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="time_tracking.surcharge_rule_created",
        entity_type="time_surcharge_rule",
        entity_id=str(rule.id),
        ip_address=request.client.host if request.client else None,
        details={"code": rule.code, "category": rule.category},
    )
    db.commit()
    db.refresh(rule)
    return rule


@router.post(
    "/time-tracking/entries/{entry_id}/surcharge-calculations",
    response_model=TimeSurchargeCalculationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_time_surcharge_calculation(
    request: Request,
    entry_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[
        AuthPrincipal, Depends(require_permission("time_tracking.surcharges.manage"))
    ],
) -> TimeSurchargeCalculationRead:
    lock_time_tracking_periods(db)
    if "time_tracking.read_all" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion.")
    entry = _get_calculation_entry(db, entry_id, principal)
    calculation = calculate_snapshot(db, entry=entry, actor_id=principal.user.id)
    db.add(calculation)
    db.flush()
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="time_tracking.surcharge_calculated",
        entity_type="time_entry",
        entity_id=str(entry.id),
        ip_address=request.client.host if request.client else None,
        details={"calculation_id": str(calculation.id), "version": calculation.version},
    )
    db.commit()
    db.refresh(calculation)
    return calculation


@router.get(
    "/time-tracking/entries/{entry_id}/surcharge-calculations",
    response_model=list[TimeSurchargeCalculationRead],
)
def list_time_surcharge_calculations(
    entry_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[
        AuthPrincipal, Depends(require_permission("time_tracking.surcharges.read"))
    ],
) -> list[TimeSurchargeCalculationRead]:
    if "time_tracking.read_all" not in principal.permission_codes:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aktion.")
    _get_calculation_entry(db, entry_id, principal)
    return db.scalars(
        select(TimeSurchargeCalculation)
        .where(TimeSurchargeCalculation.entry_id == entry_id)
        .order_by(TimeSurchargeCalculation.version)
    ).all()


@router.get("/time-tracking/periods", response_model=list[TimeTrackingPeriodRead])
def list_locked_time_periods(
    db: Annotated[Session, Depends(get_db)],
    _principal: Annotated[AuthPrincipal, Depends(require_permission("time_tracking.periods.read"))],
) -> list[TimeTrackingPeriodRead]:
    return [
        _read_period(period)
        for period in db.scalars(
            select(TimeTrackingPeriod).order_by(TimeTrackingPeriod.from_date.desc())
        ).all()
    ]


@router.post(
    "/time-tracking/periods/lock",
    response_model=TimeTrackingPeriodRead,
    status_code=status.HTTP_201_CREATED,
)
def lock_time_tracking_period(
    request: Request,
    payload: TimeTrackingPeriodLockCreate,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[AuthPrincipal, Depends(require_permission("time_tracking.periods.lock"))],
) -> TimeTrackingPeriodRead:
    lock_time_tracking_periods(db)
    schedule_settings = get_schedule_settings(db)
    zone = get_zone(schedule_settings.time_zone)
    today = datetime.now(zone).date()
    if payload.to_date >= today:
        raise HTTPException(
            status_code=409,
            detail="Eine Abrechnungsperiode kann erst nach ihrem vollständigen Ablauf gesperrt werden.",
        )
    start, end = local_period_bounds(payload.from_date, payload.to_date, zone)
    overlaps = db.scalar(
        select(TimeTrackingPeriod.id).where(
            TimeTrackingPeriod.from_date <= payload.to_date,
            TimeTrackingPeriod.to_date >= payload.from_date,
        )
    )
    if overlaps is not None:
        raise HTTPException(
            status_code=409, detail="Die Periode überschneidet eine bestehende Sperre."
        )
    entries = db.scalars(
        select(TimeEntry)
        .where(
            TimeEntry.started_at < end,
            or_(TimeEntry.ended_at.is_(None), TimeEntry.ended_at > start),
        )
        .options(
            selectinload(TimeEntry.segments),
            selectinload(TimeEntry.corrections).selectinload(TimeEntryCorrection.segments),
        )
        .order_by(TimeEntry.started_at, TimeEntry.id)
    ).all()
    unresolved = [entry for entry in entries if entry.status not in {"approved", "locked"}]
    if unresolved:
        raise HTTPException(
            status_code=409,
            detail="Die Periode enthält nicht freigegebene, abgelehnte oder laufende Zeitbuchungen.",
        )
    for entry in entries:
        if (
            as_utc(entry.started_at) < start
            or entry.ended_at is None
            or as_utc(entry.ended_at) > end
        ):
            raise HTTPException(
                status_code=409,
                detail="Eine Buchung überschreitet die Periodengrenze und muss vor der Sperre geklärt werden.",
            )
    shift_exists = select(ScheduleShift.id).where(
        ScheduleShift.status == "published",
        ScheduleShift.starts_at < end,
        ScheduleShift.ends_at > start,
    )
    missing_shift = db.scalar(
        select(
            shift_exists.where(
                ~select(TimeEntry.id)
                .where(
                    TimeEntry.shift_id == ScheduleShift.id,
                    TimeEntry.status.in_(("approved", "locked")),
                )
                .exists()
            ).exists()
        )
    )
    if missing_shift:
        raise HTTPException(
            status_code=409,
            detail="Die Periode enthält mindestens einen veröffentlichten Dienst ohne freigegebene Zeitbuchung.",
        )

    tracking_settings = get_time_tracking_settings(db)
    period = TimeTrackingPeriod(
        from_date=payload.from_date,
        to_date=payload.to_date,
        time_zone=schedule_settings.time_zone,
        federal_state=tracking_settings.federal_state,
        locked_by_id=principal.user.id,
    )
    for entry in entries:
        calculation = calculate_snapshot(
            db,
            entry=entry,
            actor_id=principal.user.id,
            permit_locked_period=True,
        )
        db.add(calculation)
    db.add(period)
    db.flush()
    add_audit_entry(
        db,
        actor_id=principal.user.id,
        action="time_tracking.period_locked",
        entity_type="time_tracking_period",
        entity_id=str(period.id),
        ip_address=request.client.host if request.client else None,
        details={
            "from_date": payload.from_date.isoformat(),
            "to_date": payload.to_date.isoformat(),
            "entry_count": len(entries),
        },
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Die Periode kollidiert mit einer parallel angelegten Abrechnungssperre.",
        ) from exc
    db.refresh(period)
    return _read_period(period)
