from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, require_permission
from app.control_room_schemas import (
    ControlRoomAbsence,
    ControlRoomBillingApproval,
    ControlRoomIncident,
    ControlRoomObject,
    ControlRoomOWKSEvent,
    ControlRoomQualification,
    ControlRoomRead,
    ControlRoomShift,
    ControlRoomTask,
)
from app.database import get_db
from app.models import (
    BillingInvoice,
    Contract,
    Employee,
    EmployeeAbsence,
    EmployeeQualification,
    Incident,
    ObjectAssignment,
    OWKSEvent,
    OWKSEventStatus,
    ScheduleShift,
    SecurityObject,
    Task,
    User,
)

router = APIRouter()
MAX_ITEMS = 100
OPEN_TASK_STATUSES = ("open", "in_progress", "blocked")
OPEN_INCIDENT_STATUSES = ("reported", "investigating", "action_required")


def _count(db: Session, query) -> int:
    return db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0


def _utc_range(day_start: date, day_end: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(day_start, time.min, tzinfo=UTC),
        datetime.combine(day_end + timedelta(days=1), time.min, tzinfo=UTC),
    )


def _assigned_employee_ids(db: Session, object_ids: list[UUID]) -> list[UUID]:
    if not object_ids:
        return []
    return list(
        db.scalars(
            select(Employee.id)
            .join(User, Employee.user_id == User.id)
            .join(ObjectAssignment, ObjectAssignment.user_id == User.id)
            .where(
                ObjectAssignment.object_id.in_(object_ids),
                Employee.archived_at.is_(None),
                Employee.employment_status == "active",
            )
            .distinct()
        ).all()
    )


@router.get(
    "/control-room",
    response_model=ControlRoomRead,
    response_model_exclude_none=True,
)
def get_control_room(
    object_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    principal: AuthPrincipal = Depends(require_permission("control_room.read")),
) -> ControlRoomRead:
    permissions = principal.permission_codes
    if "objects.read" not in permissions:
        raise HTTPException(403, "Keine Berechtigung für Objekte in der Leitstelle")

    now = datetime.now(UTC)
    start_day = from_date or (now.date() - timedelta(days=7))
    end_day = to_date or (now.date() + timedelta(days=30))
    if end_day < start_day:
        raise HTTPException(422, "Das Ende des Leitstellenzeitraums liegt vor dem Beginn.")
    if end_day == date.max:
        raise HTTPException(422, "Das Ende des Leitstellenzeitraums liegt außerhalb des Bereichs.")
    if (end_day - start_day).days > 366:
        raise HTTPException(422, "Der Leitstellenzeitraum darf höchstens 367 Tage umfassen.")
    range_start, range_end = _utc_range(start_day, end_day)

    object_query = select(SecurityObject).where(
        SecurityObject.status == "active",
        SecurityObject.archived_at.is_(None),
    )
    if "objects.read_all" not in permissions:
        object_query = object_query.where(
            SecurityObject.id.in_(
                select(ObjectAssignment.object_id).where(
                    ObjectAssignment.user_id == principal.user.id
                )
            )
        )
    allowed_objects = db.scalars(
        object_query.order_by(SecurityObject.name, SecurityObject.id)
    ).all()
    allowed_object_ids = [item.id for item in allowed_objects]
    if object_id is not None:
        if object_id not in allowed_object_ids:
            raise HTTPException(404, "Objekt nicht gefunden")
        scoped_object_ids = [object_id]
    else:
        scoped_object_ids = allowed_object_ids
    counts: dict[str, int] = {}
    objects = [
        ControlRoomObject(id=item.id, code=item.code, name=item.name) for item in allowed_objects
    ]
    counts["active_objects"] = len(objects)

    result: dict[str, object] = {
        "generated_at": now,
        "range_start": start_day,
        "range_end": end_day,
        "counts": counts,
        "objects": objects,
    }

    if "scheduling.read" in permissions:
        shifts_query = (
            select(ScheduleShift, Employee.full_name, SecurityObject.name)
            .join(Employee, ScheduleShift.employee_id == Employee.id)
            .join(SecurityObject, ScheduleShift.object_id == SecurityObject.id)
            .where(
                ScheduleShift.object_id.in_(scoped_object_ids),
                ScheduleShift.status == "published",
                ScheduleShift.starts_at <= now,
                ScheduleShift.ends_at > now,
            )
        )
        if "employees.read" not in permissions:
            shifts_query = shifts_query.where(Employee.user_id == principal.user.id)
        shifts_query = shifts_query.order_by(ScheduleShift.starts_at, ScheduleShift.id)
        shift_rows = db.execute(shifts_query.limit(MAX_ITEMS)).all()
        shifts_count = _count(db, shifts_query)
        counts["active_shifts"] = shifts_count
        result["shifts"] = [
            ControlRoomShift(
                id=shift.id,
                employee_id=shift.employee_id,
                employee_name=employee_name,
                object_id=shift.object_id,
                object_name=shift_object_name,
                starts_at=shift.starts_at,
                ends_at=shift.ends_at,
                status="published",
            )
            for shift, employee_name, shift_object_name in shift_rows
        ]

    if "owks.read" in permissions:
        latest_event_status = (
            select(OWKSEventStatus.status)
            .where(OWKSEventStatus.event_id == OWKSEvent.id)
            .order_by(OWKSEventStatus.sequence_no.desc())
            .limit(1)
            .correlate(OWKSEvent)
            .scalar_subquery()
        )
        events_query = (
            select(OWKSEvent, SecurityObject.name, latest_event_status)
            .join(SecurityObject, OWKSEvent.object_id == SecurityObject.id)
            .where(
                OWKSEvent.object_id.in_(scoped_object_ids),
                OWKSEvent.occurred_at >= range_start,
                OWKSEvent.occurred_at < range_end,
                or_(
                    OWKSEvent.event_type == "missed",
                    OWKSEvent.event_type.in_(("deviation", "manipulation", "notification"))
                    & OWKSEvent.severity.in_(("warning", "critical")),
                ),
                or_(
                    latest_event_status.is_(None),
                    latest_event_status.in_(("open", "in_progress")),
                ),
            )
            .order_by(
                case(
                    (OWKSEvent.severity == "critical", 0),
                    (OWKSEvent.severity == "warning", 1),
                    else_=2,
                ),
                OWKSEvent.occurred_at.desc(),
                OWKSEvent.id,
            )
        )
        event_rows = db.execute(events_query.limit(MAX_ITEMS)).all()
        counts["open_owks_events"] = _count(db, events_query)
        result["owks_events"] = [
            ControlRoomOWKSEvent(
                id=event.id,
                object_id=event.object_id,
                object_name=event_object_name,
                event_type=event.event_type,
                severity=event.severity,
                title=event.title,
                occurred_at=event.occurred_at,
                status=status_value or "open",
            )
            for event, event_object_name, status_value in event_rows
        ]

    if {"incidents.read", "incidents.read_all", "incidents.manage_all"} & permissions:
        incident_object_ids = scoped_object_ids
        if not {"incidents.read_all", "incidents.manage_all"} & permissions:
            assigned_object_ids = set(
                db.scalars(
                    select(ObjectAssignment.object_id).where(
                        ObjectAssignment.user_id == principal.user.id
                    )
                ).all()
            )
            incident_object_ids = [
                item_id for item_id in scoped_object_ids if item_id in assigned_object_ids
            ]
        incidents_query = (
            select(Incident, SecurityObject.name, User.full_name)
            .join(SecurityObject, Incident.object_id == SecurityObject.id)
            .join(User, Incident.assigned_to_id == User.id)
            .where(
                Incident.object_id.in_(incident_object_ids),
                Incident.status.in_(OPEN_INCIDENT_STATUSES),
            )
            .order_by(
                case(
                    (Incident.severity == "critical", 0),
                    (Incident.severity == "high", 1),
                    (Incident.severity == "medium", 2),
                    else_=3,
                ),
                Incident.due_at.asc().nulls_last(),
                Incident.created_at.desc(),
            )
        )
        incident_rows = db.execute(incidents_query.limit(MAX_ITEMS)).all()
        counts["open_incidents"] = _count(db, incidents_query)
        counts["overdue_incidents"] = _count(
            db,
            incidents_query.where(Incident.due_at < now),
        )
        result["incidents"] = [
            ControlRoomIncident(
                id=incident.id,
                title=incident.title,
                object_id=incident.object_id,
                object_name=incident_object_name,
                severity=incident.severity,
                status=incident.status,
                due_at=incident.due_at,
                assigned_to_name=assignee_name,
                created_at=incident.created_at,
            )
            for incident, incident_object_name, assignee_name in incident_rows
        ]

    task_read_permissions = {"tasks.read_own", "tasks.read_all", "tasks.manage_all"}
    if task_read_permissions & permissions:
        tasks_query = (
            select(Task, SecurityObject.name, User.full_name)
            .outerjoin(SecurityObject, Task.object_id == SecurityObject.id)
            .join(User, Task.assigned_to_id == User.id)
            .where(Task.status.in_(OPEN_TASK_STATUSES))
        )
        task_object_scope = Task.object_id.in_(scoped_object_ids)
        if object_id is None:
            task_object_scope = or_(
                task_object_scope,
                and_(
                    Task.object_id.is_(None),
                    or_(
                        Task.assigned_to_id == principal.user.id,
                        Task.created_by_id == principal.user.id,
                    ),
                ),
            )
        if not {"tasks.read_all", "tasks.manage_all"} & permissions:
            tasks_query = tasks_query.where(
                task_object_scope,
                or_(
                    Task.assigned_to_id == principal.user.id,
                    Task.created_by_id == principal.user.id,
                    Task.object_id.in_(
                        select(ObjectAssignment.object_id).where(
                            ObjectAssignment.user_id == principal.user.id
                        )
                    ),
                ),
            )
        else:
            tasks_query = tasks_query.where(task_object_scope)
        tasks_query = tasks_query.order_by(
            case(
                (Task.priority == "urgent", 0),
                (Task.priority == "high", 1),
                else_=2,
            ),
            Task.due_at.asc().nulls_last(),
            Task.created_at.desc(),
        )
        task_rows = db.execute(tasks_query.limit(MAX_ITEMS)).all()
        counts["open_tasks"] = _count(db, tasks_query)
        counts["urgent_tasks"] = _count(
            db,
            tasks_query.where((Task.priority == "urgent") | (Task.due_at < now)),
        )
        result["tasks"] = [
            ControlRoomTask(
                id=task.id,
                title=task.title,
                object_id=task.object_id,
                object_name=task_object_name,
                status=task.status,
                priority=task.priority,
                due_at=task.due_at,
                assigned_to_name=assignee_name,
                created_at=task.created_at,
            )
            for task, task_object_name, assignee_name in task_rows
        ]

    employee_ids = _assigned_employee_ids(db, scoped_object_ids)
    if "employees.absences.read" in permissions:
        absences_query = (
            select(EmployeeAbsence, Employee.full_name)
            .join(Employee, EmployeeAbsence.employee_id == Employee.id)
            .where(
                EmployeeAbsence.employee_id.in_(employee_ids),
                EmployeeAbsence.status.in_(("pending", "approved")),
                EmployeeAbsence.starts_on <= end_day,
                EmployeeAbsence.ends_on >= start_day,
            )
            .order_by(EmployeeAbsence.starts_on, EmployeeAbsence.id)
        )
        absence_rows = db.execute(absences_query.limit(MAX_ITEMS)).all()
        counts["active_absences"] = _count(db, absences_query)
        result["absences"] = [
            ControlRoomAbsence(
                employee_id=absence.employee_id,
                employee_name=employee_name,
                absence_type=absence.absence_type,
                status=absence.status,
                starts_on=absence.starts_on,
                ends_on=absence.ends_on,
            )
            for absence, employee_name in absence_rows
        ]

    if "employees.read" in permissions:
        qualifications_query = (
            select(EmployeeQualification, Employee.full_name)
            .join(Employee, EmployeeQualification.employee_id == Employee.id)
            .where(
                EmployeeQualification.employee_id.in_(employee_ids),
                EmployeeQualification.archived_at.is_(None),
                EmployeeQualification.expires_on.is_not(None),
                EmployeeQualification.expires_on <= end_day,
            )
            .order_by(EmployeeQualification.expires_on, EmployeeQualification.id)
        )
        qualification_rows = db.execute(qualifications_query.limit(MAX_ITEMS)).all()
        counts["qualification_problems"] = _count(db, qualifications_query)
        result["qualifications"] = [
            ControlRoomQualification(
                employee_id=qualification.employee_id,
                employee_name=employee_name,
                category=qualification.category,
                name=qualification.name,
                expires_on=qualification.expires_on,
            )
            for qualification, employee_name in qualification_rows
        ]

    if {"billing.invoices.read", "billing.invoices.approve"} <= permissions:
        approvals_query = (
            select(BillingInvoice, Contract.object_id, SecurityObject.name)
            .join(Contract, BillingInvoice.contract_id == Contract.id)
            .join(SecurityObject, Contract.object_id == SecurityObject.id)
            .where(
                BillingInvoice.kind == "invoice",
                BillingInvoice.status == "draft",
                BillingInvoice.archived_at.is_(None),
                Contract.object_id.in_(scoped_object_ids),
            )
            .order_by(BillingInvoice.created_at, BillingInvoice.id)
        )
        approval_rows = db.execute(approvals_query.limit(MAX_ITEMS)).all()
        counts["billing_approvals"] = _count(db, approvals_query)
        result["billing_approvals"] = [
            ControlRoomBillingApproval(
                id=invoice.id,
                invoice_number=invoice.invoice_number,
                object_name=invoice_object_name,
                issued_on=invoice.issued_on,
                created_at=invoice.created_at,
            )
            for invoice, _object_id, invoice_object_name in approval_rows
        ]

    return ControlRoomRead.model_validate(result)
