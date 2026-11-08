from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer
from app.schemas import (
    CustomerCreate,
    CustomerPage,
    CustomerRead,
    CustomerUpdate,
    DashboardRead,
)

router = APIRouter()


@router.get("/customers", response_model=CustomerPage)
def list_customers(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> CustomerPage:
    query = select(Customer)
    count_query = select(func.count()).select_from(Customer)
    if q and q.strip():
        term = f"%{q.strip()}%"
        search_filter = or_(
            Customer.company_name.ilike(term),
            Customer.customer_number.ilike(term),
            Customer.email.ilike(term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    items = db.scalars(
        query.order_by(Customer.company_name, Customer.customer_number)
        .limit(limit)
        .offset(offset)
    ).all()
    return CustomerPage(
        items=items, total=db.scalar(count_query) or 0, limit=limit, offset=offset
    )


@router.post(
    "/customers", response_model=CustomerRead, status_code=status.HTTP_201_CREATED
)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    customer = Customer(
        customer_number=f"K-{uuid4().hex.upper()}",
        company_name=payload.company_name.strip(),
        status=payload.status,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: UUID, db: Session = Depends(get_db)) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kunde nicht gefunden")
    return customer


@router.patch("/customers/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kunde nicht gefunden")

    changes = payload.model_dump(exclude_unset=True)
    if "company_name" in changes and changes["company_name"] is not None:
        changes["company_name"] = changes["company_name"].strip()
    if "email" in changes and changes["email"] is not None:
        changes["email"] = str(changes["email"])
    for field, value in changes.items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardRead:
    totals = db.execute(
        select(
            func.count(Customer.id),
            func.count().filter(Customer.status == "active"),
            func.count().filter(Customer.status == "lead"),
        )
    ).one()
    return DashboardRead(
        customers_total=totals[0],
        customers_active=totals[1],
        customers_leads=totals[2],
    )
