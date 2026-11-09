from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas import EmployeeAbsenceType, ScheduleAvailabilityRequestKind


class EmployeePortalProfileRead(BaseModel):
    full_name: str
    job_title: str | None


class EmployeePortalShiftRead(BaseModel):
    id: UUID
    object_code: str
    object_name: str
    starts_at: datetime
    ends_at: datetime
    break_minutes: int


class EmployeePortalTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    due_at: datetime | None
    priority: Literal["low", "normal", "high", "urgent"]
    status: Literal["open", "in_progress", "blocked", "completed", "cancelled"]


class EmployeePortalNotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: Literal["task.assigned", "task.status_changed"]
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None


class EmployeePortalQualificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    name: str
    issuer: str | None
    valid_from: date | None
    expires_on: date | None


class EmployeePortalTimeEntryRead(BaseModel):
    id: UUID
    started_at: datetime
    ended_at: datetime | None
    status: Literal["open", "submitted", "approved", "rejected", "correction_requested", "locked"]
    actual_work_seconds: float


class EmployeePortalTimeOverviewRead(BaseModel):
    items: list[EmployeePortalTimeEntryRead]
    total: int
    total_work_seconds: float
    limit: int
    offset: int


class EmployeePortalAbsenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    absence_type: EmployeeAbsenceType
    starts_on: date
    ends_on: date
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime


class EmployeePortalAbsenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    absence_type: EmployeeAbsenceType
    starts_on: date
    ends_on: date

    @model_validator(mode="after")
    def end_date_must_not_precede_start(self):
        if self.ends_on < self.starts_on:
            raise ValueError("Das Abwesenheitsende darf nicht vor dem Beginn liegen.")
        return self


class EmployeePortalAvailabilityRead(BaseModel):
    id: UUID
    kind: ScheduleAvailabilityRequestKind
    starts_at: datetime
    ends_at: datetime
    time_zone: str
    status: Literal["open", "accepted", "rejected"]
    created_at: datetime


class EmployeePortalAvailabilityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ScheduleAvailabilityRequestKind
    starts_at_local: datetime
    ends_at_local: datetime
    starts_at_fold: int = Field(default=0, ge=0, le=1)
    ends_at_fold: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def validate_local_interval(self):
        if self.starts_at_local.tzinfo is not None or self.ends_at_local.tzinfo is not None:
            raise ValueError("Lokale Dienstwünsche dürfen keinen UTC-Offset enthalten.")
        if self.ends_at_local <= self.starts_at_local:
            raise ValueError("Das Ende des Zeitraums muss nach dem Beginn liegen.")
        return self
