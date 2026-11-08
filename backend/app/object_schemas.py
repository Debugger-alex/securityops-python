from datetime import datetime, time
from itertools import pairwise
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

ObjectStatus = Literal["active", "inactive"]
Weekday = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class OperatingWindow(BaseModel):
    start: time
    end: time

    @model_validator(mode="after")
    def end_must_follow_start(self):
        if self.end <= self.start:
            raise ValueError("Das Ende eines Betriebszeitraums muss nach dem Beginn liegen.")
        return self


class ObjectFields(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    status: ObjectStatus = "active"
    description: str | None = Field(default=None, max_length=10000)
    service_instructions: str | None = Field(default=None, max_length=20000)
    street: str = Field(min_length=1, max_length=160)
    house_number: str = Field(min_length=1, max_length=30)
    postal_code: str = Field(min_length=1, max_length=20)
    city: str = Field(min_length=1, max_length=100)
    country_code: str = Field(default="DE", min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    operating_hours: dict[Weekday, list[OperatingWindow]] = Field(default_factory=dict)
    required_staffing: int = Field(default=1, ge=0, le=500)
    qualification_requirements: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("name", "street", "house_number", "postal_code", "city")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Dieses Pflichtfeld darf nicht leer sein.")
        return value

    @field_validator("description", "service_instructions", "phone")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @field_validator("qualification_requirements")
    @classmethod
    def normalize_qualifications(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value or len(value) > 100 for value in normalized):
            raise ValueError("Qualifikationsanforderungen müssen 1 bis 100 Zeichen lang sein.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Qualifikationsanforderungen dürfen nicht doppelt vorkommen.")
        return normalized

    @field_validator("operating_hours")
    @classmethod
    def windows_must_not_overlap(
        cls, value: dict[Weekday, list[OperatingWindow]]
    ) -> dict[Weekday, list[OperatingWindow]]:
        for windows in value.values():
            ordered = sorted(windows, key=lambda window: window.start)
            if any(current.start < previous.end for previous, current in pairwise(ordered)):
                raise ValueError(
                    "Betriebszeitfenster eines Wochentags dürfen sich nicht überschneiden."
                )
        return value


class ObjectCreate(ObjectFields):
    customer_id: UUID
    object_manager_user_id: UUID | None = None


class ObjectUpdate(BaseModel):
    customer_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: ObjectStatus | None = None
    description: str | None = Field(default=None, max_length=10000)
    service_instructions: str | None = Field(default=None, max_length=20000)
    street: str | None = Field(default=None, min_length=1, max_length=160)
    house_number: str | None = Field(default=None, min_length=1, max_length=30)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    country_code: str | None = Field(
        default=None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$"
    )
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    operating_hours: dict[Weekday, list[OperatingWindow]] | None = None
    required_staffing: int | None = Field(default=None, ge=0, le=500)
    qualification_requirements: list[str] | None = Field(default=None, max_length=30)
    object_manager_user_id: UUID | None = None

    @model_validator(mode="after")
    def supplied_required_fields_must_not_be_null(self):
        required_fields = {
            "customer_id",
            "name",
            "status",
            "street",
            "house_number",
            "postal_code",
            "city",
            "country_code",
            "operating_hours",
            "required_staffing",
            "qualification_requirements",
        }
        for field in required_fields & self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"Das Feld {field} darf nicht null sein.")
        return self

    @field_validator("name", "street", "house_number", "postal_code", "city")
    @classmethod
    def update_required_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Dieses Pflichtfeld darf nicht leer sein.")
        return value

    @field_validator("description", "service_instructions", "phone")
    @classmethod
    def normalize_optional_update_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class ObjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    customer_name: str
    object_number: str
    name: str
    status: ObjectStatus
    description: str | None
    service_instructions: str | None
    street: str
    house_number: str
    postal_code: str
    city: str
    country_code: str
    phone: str | None
    email: str | None
    operating_hours: dict[str, list[dict[str, str]]]
    required_staffing: int
    qualification_requirements: list[str]
    object_manager_user_id: UUID | None
    object_manager_name: str | None
    archived_at: datetime | None
    contacts: list["ObjectContactRead"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ObjectPage(BaseModel):
    items: list[ObjectRead]
    total: int
    limit: int
    offset: int


class ObjectContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    responsibility: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    is_primary: bool = False

    @field_validator("first_name", "last_name")
    @classmethod
    def contact_name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Vor- und Nachname dürfen nicht leer sein.")
        return value


class ObjectContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    responsibility: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    is_primary: bool | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def contact_name_update_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Vor- und Nachname dürfen nicht leer sein.")
        return value

    @model_validator(mode="after")
    def required_contact_values_must_not_be_null(self):
        for field in {"first_name", "last_name", "is_primary"} & self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"Das Feld {field} darf nicht null sein.")
        return self


class ObjectContactRead(ObjectContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class ObjectAssignmentCreate(BaseModel):
    user_id: UUID


class ObjectAssignmentRead(BaseModel):
    user_id: UUID
    username: str
    full_name: str
    assigned_at: datetime


class ObjectAssignableUserRead(BaseModel):
    id: UUID
    username: str
    full_name: str


class ObjectHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    action: str
    changed_fields: list[str]
    created_at: datetime


class ObjectSensitiveDataInput(BaseModel):
    alarm_information: str | None = Field(default=None, max_length=10000)
    emergency_information: str | None = Field(default=None, max_length=10000)
    key_management: str | None = Field(default=None, max_length=10000)
    access_authorizations: str | None = Field(default=None, max_length=10000)

    @field_validator(
        "alarm_information",
        "emergency_information",
        "key_management",
        "access_authorizations",
    )
    @classmethod
    def trim_sensitive_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class ObjectSensitiveDataRead(ObjectSensitiveDataInput):
    updated_at: datetime | None


ObjectRead.model_rebuild()
