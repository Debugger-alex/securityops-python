from datetime import date, datetime
from decimal import Decimal
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
    customer_name: str
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


EmployeeStatus = Literal["active", "inactive", "leave", "terminated"]


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_number: str = Field(min_length=1, max_length=40)
    user_id: UUID | None = None
    full_name: str = Field(min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    job_title: str | None = Field(default=None, max_length=120)
    employment_status: EmployeeStatus = "active"
    hired_on: date
    ended_on: date | None = None
    contract_type: str | None = Field(default=None, max_length=80)
    weekly_hours: Decimal | None = Field(default=None, gt=0, le=168, max_digits=5, decimal_places=2)

    @field_validator("employee_number", "full_name")
    @classmethod
    def required_values_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Personalnummer und Name dürfen nicht leer sein.")
        return value

    @field_validator("phone", "job_title", "contract_type")
    @classmethod
    def optional_values_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def end_date_must_not_precede_hire_date(self):
        if self.ended_on is not None and self.ended_on < self.hired_on:
            raise ValueError("Das Austrittsdatum darf nicht vor dem Eintrittsdatum liegen.")
        return self


class EmployeeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_number: str | None = Field(default=None, min_length=1, max_length=40)
    user_id: UUID | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    job_title: str | None = Field(default=None, max_length=120)
    employment_status: EmployeeStatus | None = None
    hired_on: date | None = None
    ended_on: date | None = None
    contract_type: str | None = Field(default=None, max_length=80)
    weekly_hours: Decimal | None = Field(default=None, gt=0, le=168, max_digits=5, decimal_places=2)

    @field_validator("employee_number", "full_name", "employment_status", "hired_on")
    @classmethod
    def required_values_must_not_be_blank_or_null(cls, value):
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Personalnummer und Name dürfen nicht leer sein.")
        return value

    @field_validator("phone", "job_title", "contract_type")
    @classmethod
    def optional_values_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def end_date_must_not_precede_hire_date(self):
        if (
            self.ended_on is not None
            and self.hired_on is not None
            and self.ended_on < self.hired_on
        ):
            raise ValueError("Das Austrittsdatum darf nicht vor dem Eintrittsdatum liegen.")
        return self


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_number: str
    user_id: UUID | None
    full_name: str
    email: EmailStr | None
    phone: str | None
    job_title: str | None
    employment_status: EmployeeStatus
    hired_on: date
    ended_on: date | None
    contract_type: str | None
    weekly_hours: Decimal | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmployeePage(BaseModel):
    items: list[EmployeeRead]
    total: int
    limit: int
    offset: int


class EmployeeSensitiveUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str | None = Field(default=None, max_length=500)
    emergency_contact: str | None = Field(default=None, max_length=300)
    internal_notes: str | None = Field(default=None, max_length=10000)

    @field_validator("address", "emergency_contact", "internal_notes")
    @classmethod
    def normalize_sensitive_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class EmployeeSensitiveRead(BaseModel):
    employee_id: UUID
    address: str | None
    emergency_contact: str | None
    internal_notes: str | None
    updated_at: datetime | None


class EmployeeQualificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    issuer: str | None = Field(default=None, max_length=160)
    valid_from: date | None = None
    expires_on: date | None = None

    @field_validator("category", "name")
    @classmethod
    def required_values_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Kategorie und Bezeichnung dürfen nicht leer sein.")
        return value

    @field_validator("issuer")
    @classmethod
    def optional_issuer_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def expiry_must_not_precede_start(self):
        if (
            self.valid_from is not None
            and self.expires_on is not None
            and self.expires_on < self.valid_from
        ):
            raise ValueError("Das Ablaufdatum darf nicht vor dem Gültigkeitsbeginn liegen.")
        return self


class EmployeeQualificationUpdate(EmployeeQualificationCreate):
    category: str | None = Field(default=None, min_length=1, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=160)

    @field_validator("category", "name")
    @classmethod
    def supplied_required_values_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        value = value.strip()
        if not value:
            raise ValueError("Kategorie und Bezeichnung dürfen nicht leer sein.")
        return value


class EmployeeQualificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    category: str
    name: str
    issuer: str | None
    valid_from: date | None
    expires_on: date | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmployeeQualificationExpiringRead(EmployeeQualificationRead):
    employee_number: str
    employee_name: str
    days_until_expiry: int


class EmployeeHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    action: str
    changed_fields: list[str]
    created_at: datetime


EmployeeAbsenceType = Literal["vacation", "sick_leave", "other"]
EmployeeAbsenceStatus = Literal["pending", "approved", "rejected"]


class EmployeeAbsenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    absence_type: EmployeeAbsenceType
    starts_on: date
    ends_on: date
    status: EmployeeAbsenceStatus = "pending"

    @model_validator(mode="after")
    def end_date_must_not_precede_start(self):
        if self.ends_on < self.starts_on:
            raise ValueError("Das Abwesenheitsende darf nicht vor dem Beginn liegen.")
        return self


class EmployeeAbsenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    absence_type: EmployeeAbsenceType | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    status: EmployeeAbsenceStatus | None = None

    @field_validator("absence_type", "starts_on", "ends_on", "status")
    @classmethod
    def supplied_values_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("Ein gesetzter Änderungswert darf nicht null sein.")
        return value

    @model_validator(mode="after")
    def end_date_must_not_precede_start(self):
        if (
            self.starts_on is not None
            and self.ends_on is not None
            and self.ends_on < self.starts_on
        ):
            raise ValueError("Das Abwesenheitsende darf nicht vor dem Beginn liegen.")
        return self


class EmployeeAbsenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    absence_type: EmployeeAbsenceType
    starts_on: date
    ends_on: date
    status: EmployeeAbsenceStatus
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime


CustomerCreate.model_rebuild()
CustomerUpdate.model_rebuild()
CustomerRead.model_rebuild()
ObjectCreate.model_rebuild()
ObjectUpdate.model_rebuild()
ObjectRead.model_rebuild()
