from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from dependencies import DBSession
from models import Order
from schemas import (
    OrderDetailRead,
    OrderRead,
    ProcessOrderRequest,
    ProcessOrderResponse,
    UpdateOrderStatusRequest,
)
from services.order_processor import OrderProcessor

router = APIRouter(prefix="/orders", tags=["orders"])

processor = OrderProcessor()


@router.get("", response_model=list[OrderRead])
async def list_orders(
    session: DBSession,
    customer_id: int | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Order]:
    """List orders with optional filters."""
    stmt = select(Order)

    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if status_filter is not None:
        stmt = stmt.where(Order.status == status_filter)

    stmt = stmt.order_by(Order.order_date.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    orders = result.scalars().unique().all()
    return list(orders)


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order_detail(
    order_id: int,
    session: DBSession,
) -> Order:
    """Return a single order with full details."""
    result = await session.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.post("/process", response_model=ProcessOrderResponse, status_code=201)
async def process_order(
    body: ProcessOrderRequest,
    session: DBSession,
) -> dict:
    """Send a transcript to be parsed by Claude and create an order."""
    try:
        result = await processor.process_order(
            customer_id=body.customer_id,
            source_type=body.source_type,
            original_message=body.original_message,
            session=session,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order processing failed: {str(e)}",
        )


@router.patch("/{order_id}/status", response_model=OrderDetailRead)
async def update_order_status(
    order_id: int,
    body: UpdateOrderStatusRequest,
    session: DBSession,
) -> Order:
    """Update an order's status (e.g. confirm, complete, cancel)."""
    result = await session.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    order.status = body.status
    if body.reviewed_by:
        order.reviewed_by = body.reviewed_by
        order.reviewed_at = datetime.now()
    order.updated_at = datetime.now()

    await session.commit()
    await session.refresh(order)

    return order
