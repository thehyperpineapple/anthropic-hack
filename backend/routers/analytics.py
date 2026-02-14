import uuid
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from dependencies import DBSession, TenantID
from models import Order, OrderItem, OrderStatus, Product
from schemas import AnalyticsSummary, OrdersByStatus, RevenueOverTime, TopProduct

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# GET /analytics/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    tenant_id: TenantID,
    session: DBSession,
    customer_id: uuid.UUID | None = None,
) -> AnalyticsSummary:
    """Aggregated dashboard stats, optionally filtered by customer."""
    filters = [Order.tenant_id == tenant_id]
    if customer_id is not None:
        filters.append(Order.customer_id == customer_id)

    stmt = select(
        func.count().label("total_orders"),
        func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue"),
        func.coalesce(func.avg(Order.total_amount), 0).label("avg_order_value"),
        func.count().filter(Order.status == OrderStatus.DRAFT).label("draft_count"),
        func.count().filter(Order.status == OrderStatus.FLAGGED).label("flagged_count"),
        func.count().filter(Order.status == OrderStatus.CONFIRMED).label("confirmed_count"),
        func.count().filter(Order.status == OrderStatus.SYNCED).label("synced_count"),
    ).where(*filters)

    result = await session.execute(stmt)
    row = result.one()

    return AnalyticsSummary(
        total_orders=row.total_orders,
        total_revenue=f"{Decimal(row.total_revenue):.2f}",
        avg_order_value=f"{Decimal(row.avg_order_value):.2f}",
        orders_by_status=OrdersByStatus(
            DRAFT=row.draft_count,
            FLAGGED=row.flagged_count,
            CONFIRMED=row.confirmed_count,
            SYNCED=row.synced_count,
        ),
        error_count=row.flagged_count,
    )


# ---------------------------------------------------------------------------
# GET /analytics/top-products
# ---------------------------------------------------------------------------

@router.get("/top-products", response_model=list[TopProduct])
async def get_top_products(
    tenant_id: TenantID,
    session: DBSession,
    limit: int = Query(default=8, ge=1, le=100),
) -> list[TopProduct]:
    """Most popular products by quantity sold (CONFIRMED/SYNCED orders only)."""
    stmt = (
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.sku.label("sku"),
            func.sum(OrderItem.quantity).label("total_qty"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.tenant_id == tenant_id,
            Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.SYNCED]),
        )
        .group_by(Product.id, Product.name, Product.sku)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        TopProduct(
            product_id=r.product_id,
            product_name=r.product_name,
            sku=r.sku,
            total_qty=int(r.total_qty),
            total_revenue=f"{Decimal(r.total_revenue):.2f}",
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /analytics/revenue-over-time
# ---------------------------------------------------------------------------

class Granularity(str, Enum):
    day = "day"
    week = "week"
    month = "month"


@router.get("/revenue-over-time", response_model=list[RevenueOverTime])
async def get_revenue_over_time(
    tenant_id: TenantID,
    session: DBSession,
    customer_id: uuid.UUID | None = None,
    granularity: Granularity = Granularity.month,
) -> list[RevenueOverTime]:
    """Revenue trend grouped by day, week, or month (CONFIRMED/SYNCED only)."""
    if granularity == Granularity.day:
        period_expr = func.date(Order.created_at)
        fmt = lambda d: str(d)  # noqa: E731
    elif granularity == Granularity.week:
        period_expr = func.date_trunc("week", Order.created_at)
        fmt = lambda d: str(d.date()) if hasattr(d, "date") else str(d)  # noqa: E731
    else:  # month
        period_expr = func.date_trunc("month", Order.created_at)
        fmt = lambda d: d.strftime("%Y-%m") if hasattr(d, "strftime") else str(d)[:7]  # noqa: E731

    filters = [
        Order.tenant_id == tenant_id,
        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.SYNCED]),
    ]
    if customer_id is not None:
        filters.append(Order.customer_id == customer_id)

    stmt = (
        select(
            period_expr.label("period"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.count().label("order_count"),
        )
        .where(*filters)
        .group_by(period_expr)
        .order_by(period_expr.asc())
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        RevenueOverTime(
            period=fmt(r.period),
            revenue=f"{Decimal(r.revenue):.2f}",
            order_count=r.order_count,
        )
        for r in rows
    ]
