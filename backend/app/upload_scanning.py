import logging
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import add_audit_entry
from app.malware_scanner import MalwareDetected, MalwareScannerError, scan_upload

logger = logging.getLogger(__name__)


def scan_upload_or_reject(
    db: Session,
    request: Request,
    *,
    content: bytes,
    actor_id: UUID,
    surface: str,
) -> None:
    try:
        scan_upload(content)
    except MalwareDetected as exc:
        _record_rejection(db, request, actor_id=actor_id, surface=surface, outcome="infected")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Die Datei wurde als unsicher erkannt und abgewiesen.",
        ) from exc
    except MalwareScannerError as exc:
        size_limit = exc.reason == "size_limit"
        logger.warning(
            "Upload-Malwareprüfung fehlgeschlagen (surface=%s, reason=%s)",
            surface,
            exc.reason,
        )
        _record_rejection(
            db,
            request,
            actor_id=actor_id,
            surface=surface,
            outcome="size_limit" if size_limit else "scan_failed",
            reason=exc.reason,
        )
        raise HTTPException(
            status_code=(
                status.HTTP_413_CONTENT_TOO_LARGE
                if size_limit
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Die Datei überschreitet das konfigurierte Scanlimit."
                if size_limit
                else "Die Dateiprüfung ist derzeit nicht verfügbar. Die Datei wurde nicht gespeichert."
            ),
        ) from exc


def _record_rejection(
    db: Session,
    request: Request,
    *,
    actor_id: UUID,
    surface: str,
    outcome: str,
    reason: str | None = None,
) -> None:
    details: dict[str, object] = {"surface": surface, "outcome": outcome}
    if reason is not None:
        details["reason"] = reason
    add_audit_entry(
        db,
        actor_id=actor_id,
        action="uploads.rejected",
        entity_type="upload",
        ip_address=request.client.host if request.client else None,
        details=details,
    )
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.error(
            "Upload-Ablehnung konnte nicht auditiert werden (surface=%s, outcome=%s)",
            surface,
            outcome,
        )
