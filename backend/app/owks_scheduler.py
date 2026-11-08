import asyncio
import logging
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine
from app.owks_api import MONITOR_ADVISORY_LOCK_KEY, monitor_due_routes

logger = logging.getLogger(__name__)
MONITOR_INTERVAL_SECONDS = 60


def run_monitoring_cycle() -> int:
    if engine.dialect.name != "postgresql":
        return 0

    with engine.connect() as connection:
        acquired = connection.scalar(
            text("SELECT pg_try_advisory_lock(:lock_key)"),
            {"lock_key": MONITOR_ADVISORY_LOCK_KEY},
        )
        connection.commit()
        if not acquired:
            return 0

        try:
            with Session(bind=connection, autoflush=False, expire_on_commit=False) as db:
                events = monitor_due_routes(db)
                db.commit()
                return len(events)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_key)"),
                {"lock_key": MONITOR_ADVISORY_LOCK_KEY},
            )
            connection.commit()


async def run_monitoring_scheduler(
    stop: asyncio.Event,
    *,
    run_cycle: Callable[[], int] = run_monitoring_cycle,
    interval_seconds: int = MONITOR_INTERVAL_SECONDS,
) -> None:
    if engine.dialect.name != "postgresql":
        return

    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
            return
        except TimeoutError:
            try:
                created_count = await asyncio.to_thread(run_cycle)
            except Exception:
                logger.exception("OWKS-Hintergrundprüfung versäumter Kontrollen fehlgeschlagen")
            else:
                if created_count:
                    logger.info(
                        "OWKS-Hintergrundprüfung hat %d versäumte Kontrolle(n) protokolliert",
                        created_count,
                    )
