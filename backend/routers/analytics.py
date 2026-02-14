from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from dependencies import DBSession
from models import Order
from schemas import AnalyticsSummary, TopProduct

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    session: DBSession,
    customer_id: int | None = None,
) -> dict:
    """Aggregated stats for dashboard cards. Pass customer_id for client view."""
    stmt = select(Order)
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)

    result = await session.execute(stmt)
    orders = list(result.scalars().all())

    total_orders = len(orders)
    total_revenue = sum(o.total_amount for o in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal("0")

    status_counts: dict[str, int] = defaultdict(int)
    error_count = 0
    for o in orders:
        status_counts[o.status] += 1
        if o.status == "error":
            error_count += 1

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "orders_by_status": dict(status_counts),
        "error_count": error_count,
    }


@router.get("/top-products", response_model=list[TopProduct])
async def get_top_products(
    session: DBSession,
    limit: int = 8,
) -> list[dict]:
    """Aggregate product demand across all orders' JSONB items."""
    result = await session.execute(select(Order))
    orders = list(result.scalars().all())

    product_map: dict[str, dict] = {}
    for order in orders:
        if not order.items:
            continue
        for item in order.items:
            sku = item.get("sku", "UNKNOWN")
            if sku not in product_map:
                product_map[sku] = {
                    "sku": sku,
                    "product_name": item.get("product_name", sku),
                    "total_qty": 0,
                    "total_revenue": Decimal("0"),
                }
            product_map[sku]["total_qty"] += item.get("quantity", 0)
            product_map[sku]["total_revenue"] += Decimal(str(item.get("line_total", 0)))

    sorted_products = sorted(
        product_map.values(), key=lambda x: x["total_qty"], reverse=True
    )
    return sorted_products[:limit]
