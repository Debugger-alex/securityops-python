from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models import NotificationOutbox, Task, TaskHistory

STATUS_NAMES = {
    "open": "Offen",
    "in_progress": "In Bearbeitung",
    "blocked": "Blockiert",
    "completed": "Erledigt",
    "cancelled": "Abgebrochen",
}


def enqueue_task_event(
    db: Session,
    task: Task,
    history: TaskHistory,
    *,
    event_type: str,
    recipient_ids: set[UUID],
    previous_assignee_id: UUID | None = None,
) -> None:
    outbox_event = NotificationOutbox(
        id=uuid4(),
        dedupe_key=f"task-history:{history.id}",
        event_type=event_type,
        aggregate_type="task",
        aggregate_id=task.id,
        payload={
            "task_id": str(task.id),
            "recipient_ids": sorted(str(recipient_id) for recipient_id in recipient_ids),
            "status": task.status,
            "title": (
                "Neue Aufgabe zugewiesen"
                if event_type == "task.assigned"
                else "Aufgabenstatus geändert"
            ),
            "body": (
                task.title
                if event_type == "task.assigned"
                else f"{task.title}: {STATUS_NAMES[task.status]}"
            ),
            "previous_assignee_id": (
                str(previous_assignee_id) if previous_assignee_id is not None else None
            ),
        },
    )
    db.add(outbox_event)
