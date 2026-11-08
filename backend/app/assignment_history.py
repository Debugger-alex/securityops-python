from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth import add_audit_entry
from app.models import EmployeeHistory, EmployeeObjectAssignmentHistory


def record_employee_object_assignment_event(
    db: Session,
    *,
    employee_id: UUID,
    object_id: UUID,
    user_id: UUID,
    actor_id: UUID,
    action: Literal["assigned", "ended"],
    ip_address: str | None,
) -> None:
    db.add(
        EmployeeObjectAssignmentHistory(
            employee_id=employee_id,
            object_id=object_id,
            user_id=user_id,
            actor_id=actor_id,
            action=action,
        )
    )
    db.add(
        EmployeeHistory(
            employee_id=employee_id,
            actor_id=actor_id,
            action=f"object_assignment_{action}",
            changed_fields=["object_assignments"],
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"employees.object_assignment_{action}",
        entity_type="employee",
        entity_id=str(employee_id),
        ip_address=ip_address,
        details={"object_id": str(object_id)},
    )
