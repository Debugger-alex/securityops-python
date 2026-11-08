from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

CustomerStatus = Literal["active", "inactive", "lead"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[str]
    permissions: list[str]


class SessionRead(BaseModel):
    user: UserRead


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role_codes: list[str] = Field(min_length=1, max_length=10)

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Der Name darf nicht leer sein.")
        return value

    @field_validator("role_codes")
    @classmethod
    def role_codes_must_be_unique(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("Rollen dürfen nicht doppelt zugewiesen werden.")
        return value


class UserUpdate(BaseModel):
    is_active: bool | None = None
    role_codes: list[str] | None = Field(default=None, min_length=1, max_length=10)

    @field_validator("is_active", "role_codes")
    @classmethod
    def update_values_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        return value

    @field_validator("role_codes")
    @classmethod
    def role_codes_must_be_unique(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and len(set(value)) != len(value):
            raise ValueError("Rollen dürfen nicht doppelt zugewiesen werden.")
        return value


class RoleRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: str
    permissions: list[str]


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class AuditLogRead(BaseModel):
    id: UUID
    actor_id: UUID | None
    action: str
    entity_type: str
    entity_id: str | None
    ip_address: str | None
    details: dict[str, object]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    status: CustomerStatus = "active"
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("company_name")
    @classmethod
    def company_name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Der Unternehmensname darf nicht leer sein.")
        return value


class CustomerUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    status: CustomerStatus | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("company_name", "status")
    @classmethod
    def required_update_values_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("Dieses Feld darf nicht null sein.")
        return value

    @field_validator("company_name")
    @classmethod
    def company_name_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Der Unternehmensname darf nicht leer sein.")
        return value


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_number: str
    company_name: str
    status: CustomerStatus
    email: str | None
    phone: str | None
    created_at: datetime
    updated_at: datetime


class CustomerPage(BaseModel):
    items: list[CustomerRead]
    total: int
    limit: int
    offset: int


class DashboardRead(BaseModel):
    customers_total: int
    customers_active: int
    customers_leads: int
