from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import add_audit_entry, require_permission
from app.database import get_db
from app.models import (
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerHistory,
    ObjectAddress,
    ObjectContact,
    ObjectHistory,
    SecurityObject,
)
from app.schemas import (
    CustomerAddressInput,
    CustomerContactCreate,
    CustomerContactRead,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerHistoryRead,
    CustomerPage,
    CustomerRead,
    CustomerStatus,
    CustomerUpdate,
    DashboardRead,
    ObjectAddressInput,
    ObjectContactCreate,
    ObjectContactRead,
    ObjectContactUpdate,
    ObjectCreate,
    ObjectHistoryRead,
    ObjectPage,
    ObjectRead,
    ObjectUpdate,
)

router = APIRouter()


def customer_query():
    return select(Customer).options(
        selectinload(Customer.addresses),
        selectinload(Customer.contacts),
    )


def get_customer_or_404(db: Session, customer_id: UUID) -> Customer:
    customer = db.scalar(customer_query().where(Customer.id == customer_id))
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kunde nicht gefunden")
    return customer


def ensure_customer_is_active(customer: Customer) -> None:
    if customer.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archivierte Kunden müssen vor Änderungen reaktiviert werden",
        )


def record_customer_event(
    db: Session,
    *,
    customer: Customer,
    actor_id: UUID,
    action: str,
    changed_fields: set[str],
    ip_address: str | None,
) -> None:
    db.add(
        CustomerHistory(
            customer_id=customer.id,
            actor_id=actor_id,
            action=action,
            changed_fields=sorted(changed_fields),
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"customers.{action}",
        entity_type="customer",
        entity_id=str(customer.id),
        ip_address=ip_address,
        details={"fields": sorted(changed_fields)},
    )


def set_customer_address(
    db: Session,
    customer: Customer,
    kind: Literal["business", "billing"],
    payload: CustomerAddressInput | None,
) -> None:
    address = next((item for item in customer.addresses if item.kind == kind), None)
    if payload is None:
        if address is not None:
            customer.addresses.remove(address)
            db.delete(address)
        return

    values = payload.model_dump()
    if address is None:
        customer.addresses.append(CustomerAddress(kind=kind, **values))
        return
    for field, value in values.items():
        setattr(address, field, value)


def object_query():
    return select(SecurityObject).options(
        selectinload(SecurityObject.customer),
        selectinload(SecurityObject.address),
        selectinload(SecurityObject.contacts),
    )


def get_object_or_404(db: Session, object_id: UUID) -> SecurityObject:
    obj = db.scalar(object_query().where(SecurityObject.id == object_id))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objekt nicht gefunden")
    return obj


def ensure_object_is_active(obj: SecurityObject) -> None:
    if obj.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archivierte Objekte müssen vor Änderungen reaktiviert werden",
        )


def record_object_event(
    db: Session,
    *,
    obj: SecurityObject,
    actor_id: UUID,
    action: str,
    changed_fields: set[str],
    ip_address: str | None,
) -> None:
    db.add(
        ObjectHistory(
            object_id=obj.id,
            actor_id=actor_id,
            action=action,
            changed_fields=sorted(changed_fields),
        )
    )
    add_audit_entry(
        db,
        actor_id=actor_id,
        action=f"objects.{action}",
        entity_type="object",
        entity_id=str(obj.id),
        ip_address=ip_address,
        details={"fields": sorted(changed_fields)},
    )


def set_object_address(
    db: Session,
    obj: SecurityObject,
    payload: ObjectAddressInput | None,
) -> None:
    if payload is None:
        if obj.address is not None:
            db.delete(obj.address)
            obj.address = None
        return

    values = payload.model_dump()
    if obj.address is None:
        obj.address = ObjectAddress(**values)
        return
    for field, value in values.items():
        setattr(obj.address, field, value)


def set_object_contact(
    db: Session,
    obj: SecurityObject,
    payload: ObjectContactCreate | None,
) -> None:
    if payload is None:
        if obj.contacts:
            for contact in list(obj.contacts):
                db.delete(contact)
                obj.contacts.remove(contact)
        return

    if obj.contacts and any(contact.is_primary for contact in obj.contacts):
        for contact in obj.contacts:
            contact.is_primary = False

    if not obj.contacts:
        obj.contacts.append(
            ObjectContact(
                first_name=payload.first_name.strip(),
                last_name=payload.last_name.strip(),
                role=payload.role.strip() if payload.role else None,
                email=str(payload.email).lower() if payload.email else None,
                phone=payload.phone.strip() if payload.phone else None,
                is_primary=payload.is_primary,
            )
        )
        return

    contact = obj.contacts[0]
    contact.first_name = payload.first_name.strip()
    contact.last_name = payload.last_name.strip()
    contact.role = payload.role.strip() if payload.role else None
    contact.email = str(payload.email).lower() if payload.email else None
    contact.phone = payload.phone.strip() if payload.phone else None
    contact.is_primary = payload.is_primary


@router.get("/customers", response_model=CustomerPage)
def list_customers(
    q: str | None = Query(default=None, max_length=200),
    customer_status: CustomerStatus | None = Query(default=None, alias="status"),
    include_archived: bool = False,
    sort_by: Literal["company_name", "customer_number", "created_at", "status"] = "company_name",
    sort_order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("customers.read")),
) -> CustomerPage:
    query = customer_query()
    count_query = select(func.count()).select_from(Customer)
    filters = []
    if not include_archived:
        filters.append(Customer.archived_at.is_(None))
    if customer_status:
        filters.append(Customer.status == customer_status)
    if q and q.strip():
        term = f"%{q.strip()}%"
        contact_matches = (
            select(CustomerContact.id)
            .where(
                CustomerContact.customer_id == Customer.id,
                or_(
                    CustomerContact.first_name.ilike(term),
                    CustomerContact.last_name.ilike(term),
                    CustomerContact.email.ilike(term),
                    CustomerContact.phone.ilike(term),
                ),
            )
            .exists()
        )
        address_matches = (
            select(CustomerAddress.id)
            .where(
                CustomerAddress.customer_id == Customer.id,
                or_(
                    CustomerAddress.city.ilike(term),
                    CustomerAddress.postal_code.ilike(term),
                ),
            )
            .exists()
        )
        filters.append(
            or_(
                Customer.company_name.ilike(term),
                Customer.customer_number.ilike(term),
                Customer.email.ilike(term),
                Customer.phone.ilike(term),
                contact_matches,
                address_matches,
            )
        )
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    sort_columns = {
        "company_name": Customer.company_name,
        "customer_number": Customer.customer_number,
        "created_at": Customer.created_at,
        "status": Customer.status,
    }
    sort_column = sort_columns[sort_by]
    sort_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    items = db.scalars(
        query.order_by(sort_expression, Customer.customer_number).limit(limit).offset(offset)
    ).all()
    return CustomerPage(items=items, total=db.scalar(count_query) or 0, limit=limit, offset=offset)


@router.post("/customers", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    request: Request,
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("customers.create")),
) -> CustomerRead:
    customer = Customer(
        customer_number=f"K-{uuid4().hex.upper()}",
        company_name=payload.company_name,
        status=payload.status,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone.strip() if payload.phone else None,
        legal_form=payload.legal_form.strip() if payload.legal_form else None,
        vat_number=payload.vat_number.strip() if payload.vat_number else None,
        tax_number=payload.tax_number.strip() if payload.tax_number else None,
        internal_notes=payload.internal_notes.strip() if payload.internal_notes else None,
    )
    db.add(customer)
    db.flush()
    if payload.business_address is not None:
        set_customer_address(db, customer, "business", payload.business_address)
    if payload.billing_address is not None:
        set_customer_address(db, customer, "billing", payload.billing_address)
    record_customer_event(
        db,
        customer=customer,
        actor_id=principal.user.id,
        action="created",
        changed_fields={
            "company_name",
            "status",
            "email",
            "phone",
            "legal_form",
            "vat_number",
            "tax_number",
            "internal_notes",
            *(["business_address"] if payload.business_address is not None else []),
            *(["billing_address"] if payload.billing_address is not None else []),
        },
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return CustomerRead.model_validate(get_customer_or_404(db, customer.id))


@router.get("/customers/{customer_id}/history", response_model=list[CustomerHistoryRead])
def list_customer_history(
    customer_id: UUID,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("customers.read")),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CustomerHistoryRead]:
    if db.get(Customer, customer_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kunde nicht gefunden")
    rows = db.scalars(
        select(CustomerHistory)
        .where(CustomerHistory.customer_id == customer_id)
        .order_by(CustomerHistory.created_at.desc(), CustomerHistory.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return [CustomerHistoryRead.model_validate(row) for row in rows]


@router.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("customers.read")),
) -> CustomerRead:
    return CustomerRead.model_validate(get_customer_or_404(db, customer_id))


@router.patch("/customers/{customer_id}", response_model=CustomerRead)
def update_customer(
    request: Request,
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("customers.update")),
) -> CustomerRead:
    customer = get_customer_or_404(db, customer_id)
    ensure_customer_is_active(customer)

    changes = payload.model_dump(
        exclude_unset=True,
        exclude={"business_address", "billing_address"},
    )
    changed_fields = set()
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
        if field == "email" and value is not None:
            value = str(value).lower()
        if getattr(customer, field) != value:
            setattr(customer, field, value)
            changed_fields.add(field)

    for kind, field in (
        ("business", "business_address"),
        ("billing", "billing_address"),
    ):
        if field in payload.model_fields_set:
            previous = next(
                (address for address in customer.addresses if address.kind == kind),
                None,
            )
            next_value = getattr(payload, field)
            previous_value = (
                {
                    key: getattr(previous, key)
                    for key in (
                        "street",
                        "house_number",
                        "postal_code",
                        "city",
                        "country_code",
                    )
                }
                if previous is not None
                else None
            )
            new_value = next_value.model_dump() if next_value is not None else None
            if previous_value != new_value:
                set_customer_address(db, customer, kind, next_value)
                changed_fields.add(field)

    if changed_fields:
        record_customer_event(
            db,
            customer=customer,
            actor_id=principal.user.id,
            action="updated",
            changed_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    return CustomerRead.model_validate(get_customer_or_404(db, customer.id))


def change_archive_state(
    customer_id: UUID,
    db: Session,
    principal,
    ip_address: str | None,
    archived: bool,
) -> CustomerRead:
    customer = get_customer_or_404(db, customer_id)
    if archived and customer.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Kunde ist bereits archiviert"
        )
    if not archived and customer.archived_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Kunde ist nicht archiviert"
        )

    customer.archived_at = datetime.now(UTC) if archived else None
    record_customer_event(
        db,
        customer=customer,
        actor_id=principal.user.id,
        action="archived" if archived else "reactivated",
        changed_fields={"archived_at"},
        ip_address=ip_address,
    )
    db.commit()
    return CustomerRead.model_validate(get_customer_or_404(db, customer.id))


@router.post("/customers/{customer_id}/archive", response_model=CustomerRead)
def archive_customer(
    request: Request,
    customer_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("customers.archive")),
) -> CustomerRead:
    return change_archive_state(
        customer_id,
        db,
        principal,
        request.client.host if request.client else None,
        archived=True,
    )


@router.post("/customers/{customer_id}/reactivate", response_model=CustomerRead)
def reactivate_customer(
    request: Request,
    customer_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("customers.archive")),
) -> CustomerRead:
    return change_archive_state(
        customer_id,
        db,
        principal,
        request.client.host if request.client else None,
        archived=False,
    )


@router.post(
    "/customers/{customer_id}/contacts",
    response_model=CustomerContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_contact(
    request: Request,
    customer_id: UUID,
    payload: CustomerContactCreate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("customers.update")),
) -> CustomerContactRead:
    customer = get_customer_or_404(db, customer_id)
    ensure_customer_is_active(customer)
    if payload.is_primary:
        for contact in customer.contacts:
            contact.is_primary = False
        db.flush()

    contact = CustomerContact(
        customer_id=customer.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        responsibility=payload.responsibility.strip() if payload.responsibility else None,
        email=str(payload.email).lower() if payload.email else None,
        phone=payload.phone.strip() if payload.phone else None,
        is_primary=payload.is_primary,
    )
    db.add(contact)
    db.flush()
    record_customer_event(
        db,
        customer=customer,
        actor_id=principal.user.id,
        action="contact_created",
        changed_fields={"contacts"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return CustomerContactRead.model_validate(contact)


@router.patch(
    "/customers/{customer_id}/contacts/{contact_id}",
    response_model=CustomerContactRead,
)
def update_customer_contact(
    request: Request,
    customer_id: UUID,
    contact_id: UUID,
    payload: CustomerContactUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("customers.update")),
) -> CustomerContactRead:
    customer = get_customer_or_404(db, customer_id)
    ensure_customer_is_active(customer)
    contact = next((item for item in customer.contacts if item.id == contact_id), None)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ansprechpartner nicht gefunden"
        )

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_primary") is True:
        for existing in customer.contacts:
            existing.is_primary = False
        db.flush()

    changed_fields = set()
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
        if field == "email" and value is not None:
            value = str(value).lower()
        if getattr(contact, field) != value:
            setattr(contact, field, value)
            changed_fields.add(field)
    if changed_fields:
        record_customer_event(
            db,
            customer=customer,
            actor_id=principal.user.id,
            action="contact_updated",
            changed_fields={"contacts"},
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    return CustomerContactRead.model_validate(contact)


@router.delete(
    "/customers/{customer_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_customer_contact(
    request: Request,
    customer_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("customers.update")),
) -> None:
    customer = get_customer_or_404(db, customer_id)
    ensure_customer_is_active(customer)
    contact = next((item for item in customer.contacts if item.id == contact_id), None)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ansprechpartner nicht gefunden"
        )
    customer.contacts.remove(contact)
    db.delete(contact)
    record_customer_event(
        db,
        customer=customer,
        actor_id=principal.user.id,
        action="contact_deleted",
        changed_fields={"contacts"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()


@router.get("/objects", response_model=ObjectPage)
def list_objects(
    q: str | None = Query(default=None, max_length=200),
    customer_id: UUID | None = Query(default=None),
    include_archived: bool = False,
    sort_by: Literal["name", "code", "created_at", "status"] = "name",
    sort_order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("objects.read")),
) -> ObjectPage:
    query = object_query()
    count_query = select(func.count()).select_from(SecurityObject)
    filters = []
    if not include_archived:
        filters.append(SecurityObject.archived_at.is_(None))
    if customer_id is not None:
        filters.append(SecurityObject.customer_id == customer_id)
    if q and q.strip():
        term = f"%{q.strip()}%"
        contact_matches = (
            select(ObjectContact.id)
            .where(
                ObjectContact.object_id == SecurityObject.id,
                or_(
                    ObjectContact.first_name.ilike(term),
                    ObjectContact.last_name.ilike(term),
                    ObjectContact.role.ilike(term),
                    ObjectContact.email.ilike(term),
                    ObjectContact.phone.ilike(term),
                ),
            )
            .exists()
        )
        address_matches = (
            select(ObjectAddress.id)
            .where(
                ObjectAddress.object_id == SecurityObject.id,
                or_(
                    ObjectAddress.city.ilike(term),
                    ObjectAddress.postal_code.ilike(term),
                    ObjectAddress.street.ilike(term),
                ),
            )
            .exists()
        )
        filters.append(
            or_(
                SecurityObject.name.ilike(term),
                SecurityObject.code.ilike(term),
                SecurityObject.object_type.ilike(term),
                SecurityObject.description.ilike(term),
                SecurityObject.emergency_contact.ilike(term),
                contact_matches,
                address_matches,
            )
        )
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    sort_columns = {
        "name": SecurityObject.name,
        "code": SecurityObject.code,
        "created_at": SecurityObject.created_at,
        "status": SecurityObject.status,
    }
    sort_expression = (
        sort_columns[sort_by].asc() if sort_order == "asc" else sort_columns[sort_by].desc()
    )
    items = db.scalars(
        query.order_by(sort_expression, SecurityObject.name).limit(limit).offset(offset)
    ).all()
    return ObjectPage(
        items=[ObjectRead.model_validate(item) for item in items],
        total=db.scalar(count_query) or 0,
        limit=limit,
        offset=offset,
    )


@router.post("/objects", response_model=ObjectRead, status_code=status.HTTP_201_CREATED)
def create_object(
    request: Request,
    payload: ObjectCreate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("objects.manage")),
) -> ObjectRead:
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kunde nicht gefunden")
    if customer.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Objekte können keinem archivierten Kunden zugeordnet werden",
        )

    code = payload.code.strip() if payload.code else f"OBJ-{uuid4().hex.upper()[:12]}"
    obj = SecurityObject(
        customer_id=customer.id,
        code=code,
        name=payload.name.strip(),
        object_type=payload.object_type.strip() if payload.object_type else None,
        description=payload.description.strip() if payload.description else None,
        status=payload.status,
        operating_hours=payload.operating_hours.strip() if payload.operating_hours else None,
        service_times=payload.service_times.strip() if payload.service_times else None,
        security_requirements=payload.security_requirements.strip()
        if payload.security_requirements
        else None,
        staffing_requirements=payload.staffing_requirements.strip()
        if payload.staffing_requirements
        else None,
        access_information=payload.access_information.strip()
        if payload.access_information
        else None,
        emergency_contact=payload.emergency_contact.strip() if payload.emergency_contact else None,
    )
    db.add(obj)
    db.flush()
    if payload.address is not None:
        set_object_address(db, obj, payload.address)
    if payload.contact is not None:
        obj.contacts.append(
            ObjectContact(
                first_name=payload.contact.first_name.strip(),
                last_name=payload.contact.last_name.strip(),
                role=payload.contact.role.strip() if payload.contact.role else None,
                email=str(payload.contact.email).lower() if payload.contact.email else None,
                phone=payload.contact.phone.strip() if payload.contact.phone else None,
                is_primary=payload.contact.is_primary,
            )
        )
    changed_fields = {"customer_id", "code", "name", "status"}
    if payload.address is not None:
        changed_fields.add("address")
    if payload.contact is not None:
        changed_fields.add("contact")

    record_object_event(
        db,
        obj=obj,
        actor_id=principal.user.id,
        action="created",
        changed_fields=changed_fields,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return ObjectRead.model_validate(get_object_or_404(db, obj.id))


@router.get("/objects/{object_id}/history", response_model=list[ObjectHistoryRead])
def list_object_history(
    object_id: UUID,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("objects.read")),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ObjectHistoryRead]:
    if db.get(SecurityObject, object_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objekt nicht gefunden")
    rows = db.scalars(
        select(ObjectHistory)
        .where(ObjectHistory.object_id == object_id)
        .order_by(ObjectHistory.created_at.desc(), ObjectHistory.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return [ObjectHistoryRead.model_validate(row) for row in rows]


@router.get("/objects/{object_id}", response_model=ObjectRead)
def get_object(
    object_id: UUID,
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("objects.read")),
) -> ObjectRead:
    return ObjectRead.model_validate(get_object_or_404(db, object_id))


@router.patch("/objects/{object_id}", response_model=ObjectRead)
def update_object(
    request: Request,
    object_id: UUID,
    payload: ObjectUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("objects.manage")),
) -> ObjectRead:
    obj = get_object_or_404(db, object_id)
    ensure_object_is_active(obj)

    if payload.customer_id is not None:
        customer = db.get(Customer, payload.customer_id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Kunde nicht gefunden"
            )
        if customer.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Objekte können keinem archivierten Kunden zugeordnet werden",
            )

    changes = payload.model_dump(exclude_unset=True, exclude={"address", "contact"})
    changed_fields = set()
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
        if (
            field
            in {
                "customer_id",
                "code",
                "name",
                "object_type",
                "description",
                "status",
                "operating_hours",
                "service_times",
                "security_requirements",
                "staffing_requirements",
                "access_information",
                "emergency_contact",
            }
            and getattr(obj, field) != value
        ):
            setattr(obj, field, value)
            changed_fields.add(field)

    if payload.address is not None:
        previous = (
            {
                "street": obj.address.street,
                "house_number": obj.address.house_number,
                "postal_code": obj.address.postal_code,
                "city": obj.address.city,
                "country_code": obj.address.country_code,
            }
            if obj.address is not None
            else None
        )
        new_value = payload.address.model_dump()
        if previous != new_value:
            set_object_address(db, obj, payload.address)
            changed_fields.add("address")
    if payload.contact is not None:
        previous = (
            {
                "first_name": obj.contacts[0].first_name,
                "last_name": obj.contacts[0].last_name,
                "role": obj.contacts[0].role,
                "email": obj.contacts[0].email,
                "phone": obj.contacts[0].phone,
                "is_primary": obj.contacts[0].is_primary,
            }
            if obj.contacts
            else None
        )
        new_value = payload.contact.model_dump()
        if previous != new_value:
            if obj.contacts:
                for contact in list(obj.contacts):
                    db.delete(contact)
                    obj.contacts.remove(contact)
            obj.contacts.append(
                ObjectContact(
                    first_name=payload.contact.first_name.strip(),
                    last_name=payload.contact.last_name.strip(),
                    role=payload.contact.role.strip() if payload.contact.role else None,
                    email=str(payload.contact.email).lower() if payload.contact.email else None,
                    phone=payload.contact.phone.strip() if payload.contact.phone else None,
                    is_primary=payload.contact.is_primary,
                )
            )
            changed_fields.add("contact")

    if changed_fields:
        record_object_event(
            db,
            obj=obj,
            actor_id=principal.user.id,
            action="updated",
            changed_fields=changed_fields,
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    return ObjectRead.model_validate(get_object_or_404(db, object_id))


def change_object_archive_state(
    object_id: UUID,
    db: Session,
    principal,
    ip_address: str | None,
    archived: bool,
) -> ObjectRead:
    obj = get_object_or_404(db, object_id)
    if archived and obj.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Objekt ist bereits archiviert",
        )
    if not archived and obj.archived_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Objekt ist nicht archiviert",
        )

    obj.archived_at = datetime.now(UTC) if archived else None
    record_object_event(
        db,
        obj=obj,
        actor_id=principal.user.id,
        action="archived" if archived else "reactivated",
        changed_fields={"archived_at"},
        ip_address=ip_address,
    )
    db.commit()
    return ObjectRead.model_validate(get_object_or_404(db, object_id))


@router.post("/objects/{object_id}/archive", response_model=ObjectRead)
def archive_object(
    request: Request,
    object_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("objects.manage")),
) -> ObjectRead:
    return change_object_archive_state(
        object_id,
        db,
        principal,
        request.client.host if request.client else None,
        archived=True,
    )


@router.post("/objects/{object_id}/reactivate", response_model=ObjectRead)
def reactivate_object(
    request: Request,
    object_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("objects.manage")),
) -> ObjectRead:
    return change_object_archive_state(
        object_id,
        db,
        principal,
        request.client.host if request.client else None,
        archived=False,
    )


@router.post(
    "/objects/{object_id}/contacts",
    response_model=ObjectContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_object_contact(
    request: Request,
    object_id: UUID,
    payload: ObjectContactCreate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("objects.manage")),
) -> ObjectContactRead:
    obj = get_object_or_404(db, object_id)
    ensure_object_is_active(obj)
    if payload.is_primary:
        for contact in obj.contacts:
            contact.is_primary = False
        db.flush()
    contact = ObjectContact(
        object_id=obj.id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        role=payload.role.strip() if payload.role else None,
        email=str(payload.email).lower() if payload.email else None,
        phone=payload.phone.strip() if payload.phone else None,
        is_primary=payload.is_primary,
    )
    db.add(contact)
    db.flush()
    record_object_event(
        db,
        obj=obj,
        actor_id=principal.user.id,
        action="contact_created",
        changed_fields={"contacts"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return ObjectContactRead.model_validate(contact)


@router.patch("/objects/{object_id}/contacts/{contact_id}", response_model=ObjectContactRead)
def update_object_contact(
    request: Request,
    object_id: UUID,
    contact_id: UUID,
    payload: ObjectContactUpdate,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("objects.manage")),
) -> ObjectContactRead:
    obj = get_object_or_404(db, object_id)
    ensure_object_is_active(obj)
    contact = next((item for item in obj.contacts if item.id == contact_id), None)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objektkontakt nicht gefunden",
        )

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_primary") is True:
        for existing in obj.contacts:
            existing.is_primary = False
        db.flush()

    changed_fields = set()
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
        if field == "email" and value is not None:
            value = str(value).lower()
        if getattr(contact, field) != value:
            setattr(contact, field, value)
            changed_fields.add(field)
    if changed_fields:
        record_object_event(
            db,
            obj=obj,
            actor_id=principal.user.id,
            action="contact_updated",
            changed_fields={"contacts"},
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    return ObjectContactRead.model_validate(contact)


@router.delete(
    "/objects/{object_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_object_contact(
    request: Request,
    object_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(require_permission("objects.manage")),
) -> None:
    obj = get_object_or_404(db, object_id)
    ensure_object_is_active(obj)
    contact = next((item for item in obj.contacts if item.id == contact_id), None)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objektkontakt nicht gefunden",
        )
    obj.contacts.remove(contact)
    db.delete(contact)
    record_object_event(
        db,
        obj=obj,
        actor_id=principal.user.id,
        action="contact_deleted",
        changed_fields={"contacts"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(
    db: Session = Depends(get_db),
    _principal=Depends(require_permission("dashboard.read")),
) -> DashboardRead:
    totals = db.execute(
        select(
            func.count(Customer.id),
            func.count().filter(Customer.status == "active"),
            func.count().filter(Customer.status == "lead"),
        ).where(Customer.archived_at.is_(None))
    ).one()
    return DashboardRead(
        customers_total=totals[0],
        customers_active=totals[1],
        customers_leads=totals[2],
    )
