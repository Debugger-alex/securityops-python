from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

CustomerStatus = Literal["active", "inactive", "lead"]


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
