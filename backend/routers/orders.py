import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from dependencies import DBSession, TenantID
from models import Anomaly, Order, OrderItem, OrderStatus
from schemas import AnomalyRead, OrderDetailRead, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
async def list_orders(
    tenant_id: TenantID,
    session: DBSession,
    customer_id: uuid.UUID | None = None,
    order_status: OrderStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[OrderRead]:
    """List orders scoped to the current tenant with optional filters."""
    stmt = (
        select(Order)
        .where(Order.tenant_id == tenant_id)
        .options(joinedload(Order.customer))
    )

    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if order_status is not None:
        stmt = stmt.where(Order.status == order_status)

    stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    orders = result.scalars().unique().all()
    return [
        OrderRead(
            id=o.id,
            customer_id=o.customer_id,
            interaction_id=o.interaction_id,
            tenant_id=o.tenant_id,
            status=o.status,
            total_amount=o.total_amount,
            created_at=o.created_at,
            customer_name=o.customer.name if o.customer else None,
        )
        for o in orders
    ]


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order_detail(
    order_id: uuid.UUID,
    tenant_id: TenantID,
    session: DBSession,
) -> OrderDetailRead:
    """Return a single order with its items, anomalies, and quotes."""
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.tenant_id == tenant_id)
        .options(
            selectinload(Order.items).joinedload(OrderItem.product),
            selectinload(Order.anomalies),
            selectinload(Order.quotes),
            joinedload(Order.customer),
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


@router.post(
    "/{order_id}/anomalies/{anomaly_id}/resolve",
    response_model=AnomalyRead,
)
async def resolve_anomaly(
    order_id: uuid.UUID,
    anomaly_id: uuid.UUID,
    tenant_id: TenantID,
    session: DBSession,
) -> Anomaly:
    """Mark an anomaly as resolved. If all anomalies on a FLAGGED order are resolved, transition to DRAFT."""
    # Verify order belongs to tenant
    order_stmt = select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    order_result = await session.execute(order_stmt)
    order = order_result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Find the anomaly
    anomaly_stmt = select(Anomaly).where(
        Anomaly.id == anomaly_id, Anomaly.order_id == order_id
    )
    anomaly_result = await session.execute(anomaly_stmt)
    anomaly = anomaly_result.scalar_one_or_none()
    if anomaly is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found")

    if anomaly.is_resolved:
        return anomaly

    anomaly.is_resolved = True

    # Check if all anomalies on this order are now resolved
    unresolved_stmt = select(Anomaly).where(
        Anomaly.order_id == order_id,
        Anomaly.is_resolved == False,  # noqa: E712
        Anomaly.id != anomaly_id,
    )
    unresolved_result = await session.execute(unresolved_stmt)
    remaining = unresolved_result.scalars().all()

    if not remaining and order.status == OrderStatus.FLAGGED:
        order.status = OrderStatus.DRAFT

    await session.commit()
    await session.refresh(anomaly)
    return anomaly
