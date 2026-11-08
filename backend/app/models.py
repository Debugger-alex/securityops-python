from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    users: Mapped[list["User"]] = relationship(secondary=user_roles, back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    roles: Mapped[list[Role]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(trim(username)) > 0", name="ck_users_username"),
        CheckConstraint("length(trim(full_name)) > 0", name="ck_users_full_name"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    roles: Mapped[list[Role]] = relationship(secondary=user_roles, back_populates="users")
    object_assignments: Mapped[list["ObjectAssignment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="ObjectAssignment.user_id",
    )
    employee_record: Mapped["Employee | None"] = relationship(back_populates="user", uselist=False)
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (Index("ix_user_sessions_user_expires", "user_id", "expires_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user: Mapped[User] = relationship(back_populates="sessions")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity_created", "entity_type", "entity_id", "created_at"),
        Index("ix_audit_logs_actor_created", "actor_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'lead')", name="ck_customers_status"),
        CheckConstraint(
            "contract_status IN ('none', 'draft', 'active', 'expired', 'terminated')",
            name="ck_customers_contract_status",
        ),
        CheckConstraint("length(trim(company_name)) > 0", name="ck_customers_company_name"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    customer_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    legal_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    contract_status: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    vat_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tax_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    addresses: Mapped[list["CustomerAddress"]] = relationship(back_populates="customer")
    contacts: Mapped[list["CustomerContact"]] = relationship(back_populates="customer")
    objects: Mapped[list["SecurityObject"]] = relationship(back_populates="customer")

    @property
    def business_address(self) -> "CustomerAddress | None":
        return next((address for address in self.addresses if address.kind == "business"), None)

    @property
    def billing_address(self) -> "CustomerAddress | None":
        return next((address for address in self.addresses if address.kind == "billing"), None)


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"
    __table_args__ = (
        UniqueConstraint("customer_id", "kind", name="uq_customer_addresses_customer_kind"),
        CheckConstraint("kind IN ('business', 'billing')", name="ck_customer_addresses_kind"),
        CheckConstraint(
            "length(trim(street)) > 0 AND length(trim(city)) > 0",
            name="ck_customer_addresses_required_fields",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    street: Mapped[str] = mapped_column(String(160), nullable=False)
    house_number: Mapped[str] = mapped_column(String(30), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), default="DE", nullable=False)
    customer: Mapped[Customer] = relationship(back_populates="addresses")


class CustomerContact(Base):
    __tablename__ = "customer_contacts"
    __table_args__ = (
        CheckConstraint(
            "length(trim(first_name)) > 0 AND length(trim(last_name)) > 0",
            name="ck_customer_contacts_name",
        ),
        Index("ix_customer_contacts_customer_name", "customer_id", "last_name", "first_name"),
        Index(
            "uq_customer_contacts_primary",
            "customer_id",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    responsibility: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    customer: Mapped[Customer] = relationship(back_populates="contacts")


class CustomerHistory(Base):
    __tablename__ = "customer_history"
    __table_args__ = (Index("ix_customer_history_customer_created", "customer_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class SecurityObject(Base):
    __tablename__ = "objects"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive')", name="ck_objects_status"),
        CheckConstraint("length(trim(name)) > 0", name="ck_objects_name"),
        CheckConstraint("length(trim(code)) > 0", name="ck_objects_code"),
        Index("ix_objects_customer_status", "customer_id", "status", "archived_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    operating_hours: Mapped[str | None] = mapped_column(String(200), nullable=True)
    service_times: Mapped[str | None] = mapped_column(String(200), nullable=True)
    staffing_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    customer: Mapped[Customer] = relationship(back_populates="objects")
    address: Mapped["ObjectAddress | None"] = relationship(
        back_populates="object", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["ObjectContact"]] = relationship(
        back_populates="object", cascade="all, delete-orphan"
    )
    history: Mapped[list["ObjectHistory"]] = relationship(
        back_populates="object", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["ObjectAssignment"]] = relationship(
        back_populates="object", cascade="all, delete-orphan"
    )
    security_details: Mapped["ObjectSecurityDetails | None"] = relationship(
        back_populates="object", cascade="all, delete-orphan", uselist=False
    )

    @property
    def customer_name(self) -> str:
        return self.customer.company_name


class ObjectAddress(Base):
    __tablename__ = "object_addresses"
    __table_args__ = (
        UniqueConstraint("object_id", name="uq_object_addresses_object"),
        CheckConstraint(
            "length(trim(street)) > 0 AND length(trim(city)) > 0",
            name="ck_object_addresses_required_fields",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    street: Mapped[str] = mapped_column(String(160), nullable=False)
    house_number: Mapped[str] = mapped_column(String(30), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), default="DE", nullable=False)
    object: Mapped[SecurityObject] = relationship(back_populates="address")


class ObjectContact(Base):
    __tablename__ = "object_contacts"
    __table_args__ = (
        CheckConstraint(
            "length(trim(first_name)) > 0 AND length(trim(last_name)) > 0",
            name="ck_object_contacts_name",
        ),
        Index("ix_object_contacts_object_name", "object_id", "last_name", "first_name"),
        Index(
            "uq_object_contacts_primary",
            "object_id",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    object: Mapped[SecurityObject] = relationship(back_populates="contacts")


class ObjectHistory(Base):
    __tablename__ = "object_history"
    __table_args__ = (Index("ix_object_history_object_created", "object_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    object: Mapped[SecurityObject] = relationship(back_populates="history")


class ObjectAssignment(Base):
    __tablename__ = "object_assignments"
    __table_args__ = (
        UniqueConstraint("object_id", "user_id", name="uq_object_assignments_object_user"),
        Index("ix_object_assignments_user_object", "user_id", "object_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    object: Mapped[SecurityObject] = relationship(back_populates="assignments")
    user: Mapped[User] = relationship(foreign_keys=[user_id], back_populates="object_assignments")


class ObjectSecurityDetails(Base):
    __tablename__ = "object_security_details"
    __table_args__ = (
        CheckConstraint(
            "security_requirements IS NULL OR length(trim(security_requirements)) > 0",
            name="ck_object_security_requirements_nonblank",
        ),
        CheckConstraint(
            "access_information IS NULL OR length(trim(access_information)) > 0",
            name="ck_object_access_information_nonblank",
        ),
    )

    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("objects.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    security_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    object: Mapped[SecurityObject] = relationship(back_populates="security_details")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint(
            "employment_status IN ('active', 'inactive', 'leave', 'terminated')",
            name="ck_employees_employment_status",
        ),
        CheckConstraint("length(trim(employee_number)) > 0", name="ck_employees_number"),
        CheckConstraint("length(trim(full_name)) > 0", name="ck_employees_full_name"),
        CheckConstraint(
            "weekly_hours IS NULL OR (weekly_hours > 0 AND weekly_hours <= 168)",
            name="ck_employees_weekly_hours",
        ),
        CheckConstraint(
            "ended_on IS NULL OR ended_on >= hired_on",
            name="ck_employees_end_date",
        ),
        Index("ix_employees_status_name", "employment_status", "full_name"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    employment_status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    hired_on: Mapped[date] = mapped_column(nullable=False)
    ended_on: Mapped[date | None] = mapped_column(nullable=True)
    contract_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    weekly_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    user: Mapped[User | None] = relationship(back_populates="employee_record")
    qualifications: Mapped[list["EmployeeQualification"]] = relationship(back_populates="employee")
    absences: Mapped[list["EmployeeAbsence"]] = relationship(back_populates="employee")
    history: Mapped[list["EmployeeHistory"]] = relationship(back_populates="employee")
    sensitive_details: Mapped["EmployeeSensitiveDetails | None"] = relationship(
        back_populates="employee", uselist=False
    )
    object_assignment_history: Mapped[list["EmployeeObjectAssignmentHistory"]] = relationship(
        back_populates="employee"
    )

    @property
    def assigned_objects(self) -> list[str]:
        if self.user is None:
            return []
        return [
            f"{assignment.object.name} ({assignment.object.code})"
            for assignment in sorted(
                self.user.object_assignments,
                key=lambda item: (item.object.name, item.object.code),
            )
        ]


class EmployeeQualification(Base):
    __tablename__ = "employee_qualifications"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_employee_qualifications_name"),
        CheckConstraint(
            "expires_on IS NULL OR valid_from IS NULL OR expires_on >= valid_from",
            name="ck_employee_qualifications_dates",
        ),
        Index("ix_employee_qualifications_expiry", "expires_on", "archived_at"),
        Index("ix_employee_qualifications_employee", "employee_id", "expires_on"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(160), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(nullable=True)
    expires_on: Mapped[date | None] = mapped_column(nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    employee: Mapped[Employee] = relationship(back_populates="qualifications")
    documents: Mapped[list["EmployeeQualificationDocument"]] = relationship(
        back_populates="qualification"
    )


class EmployeeQualificationDocument(Base):
    __tablename__ = "employee_qualification_documents"
    __table_args__ = (
        UniqueConstraint(
            "qualification_id", "version", name="uq_employee_qualification_documents_version"
        ),
        CheckConstraint("version > 0", name="ck_employee_qualification_documents_version"),
        CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 10485760",
            name="ck_employee_qualification_documents_size",
        ),
        CheckConstraint(
            "media_type IN ('application/pdf', 'image/jpeg', 'image/png')",
            name="ck_employee_qualification_documents_media_type",
        ),
        CheckConstraint(
            "length(trim(file_name)) > 0",
            name="ck_employee_qualification_documents_name",
        ),
        Index(
            "ix_employee_qualification_documents_qualification_created",
            "qualification_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    qualification_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("employee_qualifications.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    qualification: Mapped[EmployeeQualification] = relationship(back_populates="documents")


class EmployeeObjectAssignmentHistory(Base):
    __tablename__ = "employee_object_assignment_history"
    __table_args__ = (
        Index(
            "ix_employee_object_assignment_history_employee_created",
            "employee_id",
            "created_at",
        ),
        Index(
            "ix_employee_object_assignment_history_object_created",
            "object_id",
            "created_at",
        ),
        CheckConstraint(
            "action IN ('assigned', 'ended')", name="ck_employee_object_assignment_action"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    employee: Mapped[Employee] = relationship(back_populates="object_assignment_history")


class EmployeeAbsence(Base):
    __tablename__ = "employee_absences"
    __table_args__ = (
        CheckConstraint(
            "absence_type IN ('vacation', 'sick_leave', 'other')",
            name="ck_employee_absences_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_employee_absences_status",
        ),
        CheckConstraint("ends_on >= starts_on", name="ck_employee_absences_dates"),
        Index("ix_employee_absences_employee_dates", "employee_id", "starts_on", "ends_on"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    absence_type: Mapped[str] = mapped_column(String(20), nullable=False)
    starts_on: Mapped[date] = mapped_column(nullable=False)
    ends_on: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    employee: Mapped[Employee] = relationship(back_populates="absences")


class EmployeeSensitiveDetails(Base):
    __tablename__ = "employee_sensitive_details"
    __table_args__ = (
        CheckConstraint(
            "address IS NULL OR length(trim(address)) > 0",
            name="ck_employee_sensitive_address",
        ),
        CheckConstraint(
            "emergency_contact IS NULL OR length(trim(emergency_contact)) > 0",
            name="ck_employee_sensitive_emergency_contact",
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(300), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    employee: Mapped[Employee] = relationship(back_populates="sensitive_details")


class EmployeeHistory(Base):
    __tablename__ = "employee_history"
    __table_args__ = (Index("ix_employee_history_employee_created", "employee_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    employee: Mapped[Employee] = relationship(back_populates="history")


class ScheduleSettings(Base):
    __tablename__ = "schedule_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_schedule_settings_singleton"),
        CheckConstraint(
            "minimum_rest_hours >= 0 AND minimum_rest_hours <= 168",
            name="ck_schedule_settings_rest_hours",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    time_zone: Mapped[str] = mapped_column(String(80), nullable=False, default="Europe/Berlin")
    minimum_rest_hours: Mapped[int] = mapped_column(default=11, nullable=False)
    updated_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ScheduleShift(Base):
    __tablename__ = "schedule_shifts"
    __table_args__ = (
        CheckConstraint(
            "ends_at > starts_at",
            name="ck_schedule_shifts_time_order",
        ),
        CheckConstraint(
            "break_minutes >= 0",
            name="ck_schedule_shifts_break_minutes",
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'cancelled')",
            name="ck_schedule_shifts_status",
        ),
        Index("ix_schedule_shifts_employee_time", "employee_id", "starts_at", "ends_at"),
        Index("ix_schedule_shifts_object_time", "object_id", "starts_at", "ends_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    break_minutes: Mapped[int] = mapped_column(default=0, nullable=False)
    required_qualification: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    employee: Mapped[Employee] = relationship()
    object: Mapped[SecurityObject] = relationship()
    history: Mapped[list["ScheduleShiftHistory"]] = relationship(
        back_populates="shift", cascade="all, delete-orphan"
    )


class ScheduleShiftHistory(Base):
    __tablename__ = "schedule_shift_history"
    __table_args__ = (Index("ix_schedule_shift_history_shift_created", "shift_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    shift_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schedule_shifts.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    shift: Mapped[ScheduleShift] = relationship(back_populates="history")


class TimeEntry(Base):
    __tablename__ = "time_entries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'submitted', 'approved', 'rejected', "
            "'correction_requested', 'locked')",
            name="ck_time_entries_status",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="ck_time_entries_time_order",
        ),
        UniqueConstraint("employee_id", "shift_id", name="uq_time_entries_employee_shift"),
        Index("ix_time_entries_employee_start", "employee_id", "started_at"),
        Index("ix_time_entries_object_start", "object_id", "started_at"),
        Index("ix_time_entries_status_start", "status", "started_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    shift_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schedule_shifts.id", ondelete="RESTRICT"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    employee: Mapped[Employee] = relationship()
    object: Mapped[SecurityObject] = relationship()
    shift: Mapped[ScheduleShift | None] = relationship()
    segments: Mapped[list["TimeEntrySegment"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="TimeEntrySegment.position"
    )
    corrections: Mapped[list["TimeEntryCorrection"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )


class TimeEntrySegment(Base):
    __tablename__ = "time_entry_segments"
    __table_args__ = (
        CheckConstraint("kind IN ('work', 'break')", name="ck_time_entry_segments_kind"),
        CheckConstraint("position > 0", name="ck_time_entry_segments_position"),
        CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="ck_time_entry_segments_time_order",
        ),
        UniqueConstraint("entry_id", "position", name="uq_time_entry_segments_position"),
        Index("ix_time_entry_segments_entry", "entry_id", "position"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("time_entries.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry: Mapped[TimeEntry] = relationship(back_populates="segments")


class TimeEntryCorrection(Base):
    __tablename__ = "time_entry_corrections"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_time_entry_corrections_status",
        ),
        CheckConstraint(
            "length(trim(reason)) > 0",
            name="ck_time_entry_corrections_reason",
        ),
        Index("ix_time_entry_corrections_entry_created", "entry_id", "requested_at"),
        Index(
            "uq_time_entry_corrections_pending",
            "entry_id",
            unique=True,
            sqlite_where=text("status = 'pending'"),
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("time_entries.id", ondelete="RESTRICT"), nullable=False
    )
    requested_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry: Mapped[TimeEntry] = relationship(back_populates="corrections")
    segments: Mapped[list["TimeEntryCorrectionSegment"]] = relationship(
        back_populates="correction",
        cascade="all, delete-orphan",
        order_by="TimeEntryCorrectionSegment.position",
    )


class TimeEntryCorrectionSegment(Base):
    __tablename__ = "time_entry_correction_segments"
    __table_args__ = (
        CheckConstraint("kind IN ('work', 'break')", name="ck_time_entry_correction_segments_kind"),
        CheckConstraint("position > 0", name="ck_time_entry_correction_segments_position"),
        CheckConstraint(
            "ended_at > started_at",
            name="ck_time_entry_correction_segments_time_order",
        ),
        UniqueConstraint("correction_id", "position", name="uq_time_entry_correction_segments_pos"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    correction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("time_entry_corrections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correction: Mapped[TimeEntryCorrection] = relationship(back_populates="segments")


class TimeEntryHistory(Base):
    __tablename__ = "time_entry_history"
    __table_args__ = (Index("ix_time_entry_history_entry_created", "entry_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("time_entries.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class TimeTrackingSettings(Base):
    __tablename__ = "time_tracking_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_time_tracking_settings_singleton"),
        CheckConstraint(
            "federal_state IS NULL OR federal_state IN "
            "('BW', 'BY', 'BE', 'BB', 'HB', 'HH', 'HE', 'MV', 'NI', 'NW', 'RP', 'SL', 'SN', 'ST', 'SH', 'TH')",
            name="ck_time_tracking_settings_federal_state",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    federal_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    updated_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class TimeSurchargeRule(Base):
    __tablename__ = "time_surcharge_rules"
    __table_args__ = (
        CheckConstraint(
            "category IN ('night', 'saturday', 'sunday', 'public_holiday', 'business')",
            name="ck_time_surcharge_rules_category",
        ),
        CheckConstraint(
            "calculation_type IN ('percentage', 'fixed')",
            name="ck_time_surcharge_rules_calculation_type",
        ),
        CheckConstraint("value > 0", name="ck_time_surcharge_rules_value"),
        CheckConstraint(
            "valid_to IS NULL OR valid_to >= valid_from",
            name="ck_time_surcharge_rules_validity",
        ),
        CheckConstraint(
            "combination_mode IN ('exclusive', 'combine')",
            name="ck_time_surcharge_rules_combination",
        ),
        UniqueConstraint("code", name="uq_time_surcharge_rules_code"),
        Index("ix_time_surcharge_rules_validity", "valid_from", "valid_to"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    calculation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    basis_description: Mapped[str] = mapped_column(String(240), nullable=False)
    valid_from: Mapped[date] = mapped_column(nullable=False)
    valid_to: Mapped[date | None] = mapped_column(nullable=True)
    priority: Mapped[int] = mapped_column(nullable=False, default=100)
    combination_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="exclusive")
    weekdays: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    starts_local: Mapped[str | None] = mapped_column(String(5), nullable=True)
    ends_local: Mapped[str | None] = mapped_column(String(5), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class TimeSurchargeCalculation(Base):
    __tablename__ = "time_surcharge_calculations"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_time_surcharge_calculations_version"),
        CheckConstraint(
            "length(gross_work_seconds) > 0",
            name="ck_time_surcharge_calculations_work_seconds",
        ),
        UniqueConstraint("entry_id", "version", name="uq_time_surcharge_calculations_version"),
        Index("ix_time_surcharge_calculations_entry_created", "entry_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("time_entries.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(nullable=False)
    gross_work_seconds: Mapped[str] = mapped_column(String(32), nullable=False)
    time_zone: Mapped[str] = mapped_column(String(80), nullable=False)
    federal_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    rule_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    allocation_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    source_segments: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class TimeTrackingPeriod(Base):
    __tablename__ = "time_tracking_periods"
    __table_args__ = (
        CheckConstraint("to_date >= from_date", name="ck_time_tracking_periods_date_order"),
        UniqueConstraint("from_date", "to_date", name="uq_time_tracking_periods_range"),
        Index("ix_time_tracking_periods_range", "from_date", "to_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    from_date: Mapped[date] = mapped_column(nullable=False)
    to_date: Mapped[date] = mapped_column(nullable=False)
    time_zone: Mapped[str] = mapped_column(String(80), nullable=False)
    federal_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    locked_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    locked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class OWKSControlPoint(Base):
    __tablename__ = "owks_control_points"
    __table_args__ = (
        CheckConstraint("identifier_type IN ('qr', 'nfc')", name="ck_owks_control_point_type"),
        CheckConstraint("length(trim(name)) > 0", name="ck_owks_control_point_name"),
        Index("ix_owks_control_points_object_active", "object_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    identifier_type: Mapped[str] = mapped_column(String(10), nullable=False)
    identifier_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class OWKSRoute(Base):
    __tablename__ = "owks_routes"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_owks_route_name"),
        CheckConstraint("interval_minutes > 0", name="ck_owks_route_interval"),
        Index("ix_owks_routes_object_active", "object_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    interval_minutes: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class OWKSRoutePoint(Base):
    __tablename__ = "owks_route_points"
    __table_args__ = (
        UniqueConstraint("route_id", "position", name="uq_owks_route_points_position"),
        UniqueConstraint("route_id", "control_point_id", name="uq_owks_route_points_point"),
        CheckConstraint("position >= 0", name="ck_owks_route_points_position"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    route_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("owks_routes.id", ondelete="RESTRICT"), nullable=False
    )
    control_point_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("owks_control_points.id", ondelete="RESTRICT"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(nullable=False)


class OWKSChallenge(Base):
    __tablename__ = "owks_challenges"
    __table_args__ = (Index("ix_owks_challenges_expires", "expires_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class OWKSEvent(Base):
    __tablename__ = "owks_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('entry', 'handover', 'control', 'manipulation', 'deviation', 'missed', 'notification', 'correction')",
            name="ck_owks_events_type",
        ),
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')", name="ck_owks_events_severity"
        ),
        CheckConstraint("sync_status IN ('synced', 'conflict')", name="ck_owks_events_sync_status"),
        UniqueConstraint("actor_id", "client_event_id", name="uq_owks_events_idempotency"),
        Index("ix_owks_events_object_occurred", "object_id", "occurred_at"),
        Index("ix_owks_events_object_created", "object_id", "created_at"),
        Index(
            "uq_owks_missed_event_client_id",
            "client_event_id",
            unique=True,
            postgresql_where=text("event_type = 'missed'"),
            sqlite_where=text("event_type = 'missed'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    object_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
    )
    route_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("owks_routes.id", ondelete="RESTRICT"), nullable=True
    )
    control_point_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("owks_control_points.id", ondelete="RESTRICT"), nullable=True
    )
    corrects_event_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("owks_events.id", ondelete="RESTRICT"), nullable=True
    )
    employee_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=True
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    challenge_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("owks_challenges.id", ondelete="RESTRICT"), nullable=True
    )
    client_event_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), default="synced", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class OWKSEventStatus(Base):
    __tablename__ = "owks_event_statuses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved')", name="ck_owks_event_status"
        ),
        CheckConstraint("sequence_no > 0", name="ck_owks_event_status_sequence"),
        UniqueConstraint("event_id", "sequence_no", name="uq_owks_event_status_sequence"),
        Index("ix_owks_event_statuses_event_created", "event_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("owks_events.id", ondelete="RESTRICT"), nullable=False
    )
    sequence_no: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class OWKSAttachment(Base):
    __tablename__ = "owks_attachments"
    __table_args__ = (
        CheckConstraint(
            "media_type IN ('application/pdf', 'image/jpeg', 'image/png')",
            name="ck_owks_attachments_media_type",
        ),
        CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 10485760", name="ck_owks_attachments_size"
        ),
        Index("ix_owks_attachments_event_created", "event_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("owks_events.id", ondelete="RESTRICT"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
