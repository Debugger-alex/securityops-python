from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
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
        CheckConstraint("length(trim(company_name)) > 0", name="ck_customers_company_name"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    customer_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    legal_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
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
    security_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    staffing_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
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
