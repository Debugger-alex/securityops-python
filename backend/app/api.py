from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import add_audit_entry, require_permission
from app.database import get_db
from app.models import Customer, CustomerAddress, CustomerContact, CustomerHistory
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
