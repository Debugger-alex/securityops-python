from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

CustomerStatus = Literal["active", "inactive", "lead"]
ObjectStatus = Literal["active", "inactive"]


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
    legal_form: str | None = Field(default=None, max_length=100)
    vat_number: str | None = Field(default=None, max_length=32)
    tax_number: str | None = Field(default=None, max_length=32)
    internal_notes: str | None = Field(default=None, max_length=10000)
    business_address: "CustomerAddressInput | None" = None
    billing_address: "CustomerAddressInput | None" = None

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
    legal_form: str | None = Field(default=None, max_length=100)
    vat_number: str | None = Field(default=None, max_length=32)
    tax_number: str | None = Field(default=None, max_length=32)
    internal_notes: str | None = Field(default=None, max_length=10000)
    business_address: "CustomerAddressInput | None" = None
    billing_address: "CustomerAddressInput | None" = None

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
    legal_form: str | None
    vat_number: str | None
    tax_number: str | None
    internal_notes: str | None
    archived_at: datetime | None
    business_address: "CustomerAddressRead | None"
    billing_address: "CustomerAddressRead | None"
    contacts: list["CustomerContactRead"] = Field(default_factory=list)
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


class CustomerAddressInput(BaseModel):
    street: str = Field(min_length=1, max_length=160)
    house_number: str = Field(min_length=1, max_length=30)
    postal_code: str = Field(min_length=1, max_length=20)
    city: str = Field(min_length=1, max_length=100)
    country_code: str = Field(default="DE", min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")

    @field_validator("street", "house_number", "postal_code", "city")
    @classmethod
    def address_values_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Adressfelder dürfen nicht leer sein.")
        return value


class CustomerAddressRead(CustomerAddressInput):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class CustomerContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    responsibility: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    is_primary: bool = False

    @field_validator("first_name", "last_name")
    @classmethod
    def contact_names_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name und Nachname dürfen nicht leer sein.")
        return value


class CustomerContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    responsibility: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    is_primary: bool | None = None

    @field_validator("first_name", "last_name", "is_primary")
    @classmethod
    def non_nullable_contact_fields_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        return value


class CustomerContactRead(CustomerContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class CustomerHistoryRead(BaseModel):
    id: UUID
    actor_id: UUID | None
    action: str
    changed_fields: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObjectAddressInput(BaseModel):
    street: str = Field(min_length=1, max_length=160)
    house_number: str = Field(min_length=1, max_length=30)
    postal_code: str = Field(min_length=1, max_length=20)
    city: str = Field(min_length=1, max_length=100)
    country_code: str = Field(default="DE", min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")

    @field_validator("street", "house_number", "postal_code", "city")
    @classmethod
    def address_values_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Adressfelder dürfen nicht leer sein.")
        return value


class ObjectAddressRead(ObjectAddressInput):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class ObjectContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    is_primary: bool = False

    @field_validator("first_name", "last_name")
    @classmethod
    def contact_names_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Vor- und Nachname dürfen nicht leer sein.")
        return value


class ObjectContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    is_primary: bool | None = None

    @field_validator("first_name", "last_name", "is_primary")
    @classmethod
    def non_nullable_contact_fields_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        return value


class ObjectContactRead(ObjectContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class ObjectAssignmentCandidateRead(BaseModel):
    id: UUID
    username: str
    full_name: str


class ObjectAssignmentRead(BaseModel):
    user_id: UUID
    username: str
    full_name: str
    assigned_at: datetime


class ObjectAssignmentUpdate(BaseModel):
    user_ids: list[UUID] = Field(max_length=200)

    @field_validator("user_ids")
    @classmethod
    def assignment_users_must_be_unique(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Benutzer dürfen einem Objekt nicht doppelt zugewiesen werden.")
        return value


class ObjectSecurityUpdate(BaseModel):
    security_requirements: str | None = Field(default=None, max_length=10000)
    access_information: str | None = Field(default=None, max_length=10000)
    emergency_contact: str | None = Field(default=None, max_length=200)

    @field_validator("security_requirements", "access_information", "emergency_contact")
    @classmethod
    def normalize_sensitive_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ObjectSecurityRead(BaseModel):
    object_id: UUID
    security_requirements: str | None
    access_information: str | None
    emergency_contact: str | None
    updated_at: datetime | None


class ObjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID
    name: str = Field(min_length=1, max_length=200)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    object_type: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=10000)
    status: ObjectStatus = "active"
    operating_hours: str | None = Field(default=None, max_length=200)
    service_times: str | None = Field(default=None, max_length=200)
    staffing_requirements: str | None = Field(default=None, max_length=10000)
    address: ObjectAddressInput | None = None
    contact: ObjectContactCreate | None = None
    contacts: list[ObjectContactCreate] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def at_most_one_primary_contact(self):
        primary_count = sum(contact.is_primary for contact in self.contacts)
        primary_count += int(self.contact.is_primary) if self.contact is not None else 0
        if primary_count > 1:
            raise ValueError("Für ein Objekt darf nur ein Primärkontakt gesetzt sein.")
        return self

    @field_validator("name", "code")
    @classmethod
    def values_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name und Code dürfen nicht leer sein.")
        return value


class ObjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    object_type: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=10000)
    status: ObjectStatus | None = None
    operating_hours: str | None = Field(default=None, max_length=200)
    service_times: str | None = Field(default=None, max_length=200)
    staffing_requirements: str | None = Field(default=None, max_length=10000)
    address: ObjectAddressInput | None = None

    @field_validator("name", "code")
    @classmethod
    def values_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name und Code dürfen nicht leer sein.")
        return value


class ObjectHistoryRead(BaseModel):
    id: UUID
    actor_id: UUID | None
    action: str
    changed_fields: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    code: str
    name: str
    object_type: str | None
    description: str | None
    status: ObjectStatus
    operating_hours: str | None
    service_times: str | None
    staffing_requirements: str | None
    archived_at: datetime | None
    address: ObjectAddressRead | None
    contacts: list[ObjectContactRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ObjectPage(BaseModel):
    items: list[ObjectRead]
    total: int
    limit: int
    offset: int


CustomerCreate.model_rebuild()
CustomerUpdate.model_rebuild()
CustomerRead.model_rebuild()
ObjectCreate.model_rebuild()
ObjectUpdate.model_rebuild()
ObjectRead.model_rebuild()
