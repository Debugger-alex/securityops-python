from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BillingKind = Literal["hourly", "flat", "surcharge"]
InvoiceKind = Literal["invoice", "correction", "cancellation"]


def nonblank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Dieses Feld darf nicht leer sein.")
    return value


class BillingRateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    kind: BillingKind
    unit: str = Field(min_length=1, max_length=40)
    unit_price: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    tax_code: str = Field(min_length=1, max_length=40)
    tax_rate: Decimal = Field(ge=0, le=100, max_digits=7, decimal_places=4)
    currency: str = Field(default="EUR", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @field_validator("code", "name", "unit", "tax_code")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        return nonblank(value)


class BillingRateRead(BaseModel):
    id: UUID
    code: str
    name: str
    kind: BillingKind
    unit: str
    unit_price: Decimal
    tax_code: str
    tax_rate: Decimal
    currency: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class InvoiceLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rate_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=4)
    description: str | None = Field(default=None, max_length=240)
    source_time_entry_ids: list[UUID] = Field(default_factory=list, max_length=100)

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str | None) -> str | None:
        return nonblank(value) if value is not None else None


class InvoiceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    customer_id: UUID
    contract_id: UUID | None = None
    issued_on: date
    due_on: date
    lines: list[InvoiceLineCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_request(self):
        if self.due_on < self.issued_on:
            raise ValueError("Das Fälligkeitsdatum darf nicht vor dem Rechnungsdatum liegen.")
        source_ids = [entry for line in self.lines for entry in line.source_time_entry_ids]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("Eine Zeitbuchung darf nicht mehrfach zugeordnet werden.")
        return self


class InvoiceCorrectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    reason: str = Field(min_length=1, max_length=2000)
    issued_on: date
    due_on: date
    replacement_lines: list[InvoiceLineCreate] = Field(default_factory=list, max_length=100)

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        return nonblank(value)

    @model_validator(mode="after")
    def due_date_is_not_before_issue(self):
        if self.due_on < self.issued_on:
            raise ValueError("Das Fälligkeitsdatum darf nicht vor dem Rechnungsdatum liegen.")
        return self


class InvoiceLineRead(BaseModel):
    id: UUID
    position: int
    description: str
    kind: BillingKind
    quantity: Decimal
    unit: str
    unit_price: Decimal
    tax_code: str
    tax_rate: Decimal
    net_amount: Decimal
    tax_amount: Decimal
    gross_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceRead(BaseModel):
    id: UUID
    invoice_number: str
    customer_id: UUID
    contract_id: UUID | None
    kind: InvoiceKind
    status: Literal["draft", "approved", "archived"]
    payment_status: Literal["open", "partial", "paid"]
    dunning_status: Literal["none", "reminder_1", "reminder_2", "final"]
    currency: str
    issued_on: date
    due_on: date
    correction_of_id: UUID | None
    correction_reason: str | None
    net_amount: Decimal
    tax_amount: Decimal
    gross_amount: Decimal
    approved_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    lines: list[InvoiceLineRead]

    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    paid_on: date
    reference: str | None = Field(default=None, max_length=160)

    @field_validator("reference")
    @classmethod
    def normalize_reference(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class DunningUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["none", "reminder_1", "reminder_2", "final"]
    note: str = Field(min_length=1, max_length=1000)

    @field_validator("note")
    @classmethod
    def note_must_not_be_blank(cls, value: str) -> str:
        return nonblank(value)


class ArchiveInvoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=1000)

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        return nonblank(value)


class BillingPaymentRead(BaseModel):
    id: UUID
    invoice_id: UUID
    amount: Decimal
    paid_on: date
    reference: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BillingExportRead(BaseModel):
    id: UUID
    invoice_id: UUID
    format_version: str
    payload: dict[str, object]
    payload_sha256: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
