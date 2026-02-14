import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dependencies import DBSession, TenantID
from models import Order, OrderStatus
from schemas import OrderDetailRead, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
async def list_orders(
    tenant_id: TenantID,
    session: DBSession,
    customer_id: uuid.UUID | None = None,
    order_status: OrderStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Order]:
    """List orders scoped to the current tenant with optional filters."""
    stmt = select(Order).where(Order.tenant_id == tenant_id)

    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if order_status is not None:
        stmt = stmt.where(Order.status == order_status)

    stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order_detail(
    order_id: uuid.UUID,
    tenant_id: TenantID,
    session: DBSession,
) -> Order:
    """Return a single order with its items, anomalies, and quotes."""
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.tenant_id == tenant_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.anomalies),
            selectinload(Order.quotes),
        )
    )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.post("/{order_id}/confirm", response_model=OrderDetailRead)
async def confirm_order(
    order_id: uuid.UUID,
    tenant_id: TenantID,
    session: DBSession,
) -> Order:
    """Manually approve a DRAFT or FLAGGED order -> CONFIRMED."""
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.tenant_id == tenant_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.anomalies),
            selectinload(Order.quotes),
        )
    )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status not in (OrderStatus.DRAFT, OrderStatus.FLAGGED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot confirm order in '{order.status.value}' status",
        )

    order.status = OrderStatus.CONFIRMED
    await session.commit()
    await session.refresh(order)

    return order
