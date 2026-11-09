from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

TaskPriority = Literal["low", "normal", "high", "urgent"]
TaskStatus = Literal["open", "in_progress", "blocked", "completed", "cancelled"]


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    assigned_to_id: UUID | None = None
    customer_id: UUID | None = None
    object_id: UUID | None = None
    due_at: datetime | None = None
    priority: TaskPriority = "normal"

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Der Aufgabentitel darf nicht leer sein.")
        return value

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Die Beschreibung darf nicht leer sein.")
        return value

    @field_validator("due_at")
    @classmethod
    def due_at_must_include_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("Die Fälligkeit muss eine Zeitzone enthalten.")
        return value


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    assigned_to_id: UUID | None = None
    customer_id: UUID | None = None
    object_id: UUID | None = None
    due_at: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    completion_evidence: str | None = Field(default=None, max_length=10000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Der Aufgabentitel darf nicht leer sein.")
        return value

    @field_validator("description", "completion_evidence")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Der Text darf nicht leer sein.")
        return value

    @field_validator("due_at")
    @classmethod
    def due_at_must_include_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("Die Fälligkeit muss eine Zeitzone enthalten.")
        return value


class TaskCommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1, max_length=5000)

    @field_validator("body")
    @classmethod
    def body_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Der Kommentar darf nicht leer sein.")
        return value


class TaskRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    assigned_to_id: UUID
    assigned_to_name: str
    created_by_id: UUID | None
    created_by_name: str | None
    customer_id: UUID | None
    customer_name: str | None
    object_id: UUID | None
    object_name: str | None
    due_at: datetime | None
    priority: TaskPriority
    status: TaskStatus
    completion_evidence: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskCommentRead(BaseModel):
    id: UUID
    author_id: UUID | None
    author_name: str | None
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskHistoryRead(BaseModel):
    id: UUID
    actor_id: UUID | None
    actor_name: str | None
    action: str
    changes: dict[str, object]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskDetail(TaskRead):
    comments: list[TaskCommentRead]
    history: list[TaskHistoryRead]


class TaskPage(BaseModel):
    items: list[TaskRead]
    total: int
    limit: int
    offset: int


class TaskAssigneeRead(BaseModel):
    id: UUID
    full_name: str


class TaskCustomerChoice(BaseModel):
    id: UUID
    company_name: str


class TaskObjectChoice(BaseModel):
    id: UUID
    name: str
    customer_id: UUID
    customer_name: str


class TaskLocationsRead(BaseModel):
    customers: list[TaskCustomerChoice]
    objects: list[TaskObjectChoice]
