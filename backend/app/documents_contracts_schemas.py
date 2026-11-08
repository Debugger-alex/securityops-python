from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DocumentStatus = Literal["draft", "active", "expired", "archived"]
ContractType = Literal["customer", "object", "personnel", "service", "additional", "other"]
ContractStatus = Literal["draft", "active", "terminated", "expired", "archived"]
ApprovalStatus = Literal["pending", "approved", "rejected"]
ReminderStatus = Literal["open", "completed", "dismissed"]


class DocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_number: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    category: str = Field(min_length=1, max_length=80)
    status: Literal["draft", "active"] = "active"
    customer_id: UUID | None = None
    object_id: UUID | None = None
    employee_id: UUID | None = None
    expires_on: date | None = None

    @field_validator("document_number", "title", "category")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Dieses Feld darf nicht leer sein.")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_number: str | None = Field(default=None, min_length=1, max_length=80)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    status: Literal["draft", "active", "expired"] | None = None
    customer_id: UUID | None = None
    object_id: UUID | None = None
    employee_id: UUID | None = None
    expires_on: date | None = None

    @field_validator("document_number", "title", "category", "status")
    @classmethod
    def required_update_values_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Dieses Feld darf nicht leer sein.")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class DocumentVersionRead(BaseModel):
    id: UUID
    document_id: UUID
    version: int
    file_name: str
    media_type: str
    size_bytes: int
    sha256: str
    uploaded_by_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentApprovalRead(BaseModel):
    id: UUID
    version_id: UUID
    requested_by_id: UUID | None
    decided_by_id: UUID | None
    status: ApprovalStatus
    decision_note: str | None
    created_at: datetime
    decided_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DocumentApprovalQueueItem(DocumentApprovalRead):
    document_id: UUID
    document_number: str
    document_title: str
    version: int


class DocumentReadReceiptRead(BaseModel):
    id: UUID
    version_id: UUID
    user_id: UUID
    read_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentHistoryRead(BaseModel):
    id: UUID
    actor_id: UUID | None
    action: str
    changed_fields: list[str]
    details: dict[str, object]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: UUID
    document_number: str
    title: str
    description: str | None
    category: str
    status: DocumentStatus
    customer_id: UUID | None
    object_id: UUID | None
    employee_id: UUID | None
    expires_on: date | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    latest_version: DocumentVersionRead | None

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailRead(DocumentRead):
    versions: list[DocumentVersionRead]
    approvals: list[DocumentApprovalRead]
    read_receipts: list[DocumentReadReceiptRead]
    history: list[DocumentHistoryRead]


class DocumentPage(BaseModel):
    items: list[DocumentRead]
    total: int
    limit: int
    offset: int


class ApprovalDecision(BaseModel):
    status: Literal["approved", "rejected"]
    decision_note: str | None = Field(default=None, max_length=2000)

    @field_validator("decision_note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class ContractCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_number: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    contract_type: ContractType
    counterparty: str = Field(min_length=1, max_length=200)
    customer_id: UUID
    object_id: UUID | None = None
    employee_id: UUID | None = None
    starts_on: date
    ends_on: date | None = None
    notice_period_days: int | None = Field(default=None, ge=0, le=3650)
    renewal_rule: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "active", "terminated", "expired"] = "draft"
    document_id: UUID | None = None
    internal_notes: str | None = Field(default=None, max_length=10000)

    @field_validator("contract_number", "name", "counterparty")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Dieses Feld darf nicht leer sein.")
        return value

    @field_validator("renewal_rule", "internal_notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def dates_must_be_consistent(self):
        if self.ends_on is not None and self.ends_on < self.starts_on:
            raise ValueError("Das Vertragsende darf nicht vor dem Vertragsbeginn liegen.")
        if self.object_id is not None and self.contract_type not in {"object", "service"}:
            raise ValueError(
                "Ein Objekt darf nur Objekt- oder Dienstleistungsverträgen zugeordnet sein."
            )
        return self


class ContractUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_number: str | None = Field(default=None, min_length=1, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    contract_type: ContractType | None = None
    counterparty: str | None = Field(default=None, min_length=1, max_length=200)
    customer_id: UUID | None = None
    object_id: UUID | None = None
    employee_id: UUID | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    notice_period_days: int | None = Field(default=None, ge=0, le=3650)
    renewal_rule: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "active", "terminated", "expired"] | None = None
    document_id: UUID | None = None
    internal_notes: str | None = Field(default=None, max_length=10000)

    @field_validator(
        "contract_number", "name", "contract_type", "counterparty", "starts_on", "status"
    )
    @classmethod
    def required_update_values_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Dieses Feld darf nicht leer sein.")
        return value

    @field_validator("renewal_rule", "internal_notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class ContractHistoryRead(BaseModel):
    id: UUID
    actor_id: UUID | None
    action: str
    changed_fields: list[str]
    details: dict[str, object]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractRead(BaseModel):
    id: UUID
    contract_number: str
    name: str
    contract_type: ContractType
    counterparty: str
    customer_id: UUID
    object_id: UUID | None
    employee_id: UUID | None
    starts_on: date
    ends_on: date | None
    notice_period_days: int | None
    renewal_rule: str | None
    status: ContractStatus
    document_id: UUID | None
    internal_notes: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    history: list[ContractHistoryRead] = Field(default_factory=list)


class ContractPage(BaseModel):
    items: list[ContractRead]
    total: int
    limit: int
    offset: int


class ReminderSettingsRead(BaseModel):
    lead_days: list[int]
    updated_by_id: UUID | None
    updated_at: datetime | None


class ReminderSettingsUpdate(BaseModel):
    lead_days: list[int] = Field(min_length=1, max_length=12)

    @field_validator("lead_days")
    @classmethod
    def lead_days_must_be_unique_and_bounded(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 3650 for day in value):
            raise ValueError("Vorlaufzeiten müssen zwischen 0 und 3650 Tagen liegen.")
        if len(set(value)) != len(value):
            raise ValueError("Vorlaufzeiten dürfen nicht doppelt vorkommen.")
        return sorted(value, reverse=True)


class ReminderStatusUpdate(BaseModel):
    status: Literal["completed", "dismissed"]


class ReminderRead(BaseModel):
    id: UUID
    document_id: UUID | None
    contract_id: UUID | None
    reminder_type: Literal[
        "document_expiry",
        "contract_expiry",
        "contract_termination",
        "contract_renewal",
    ]
    event_on: date
    remind_on: date
    status: ReminderStatus
    created_at: datetime
    subject: str
    number: str

    model_config = ConfigDict(from_attributes=True)
