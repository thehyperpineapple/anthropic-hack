import logging
import uuid
from decimal import Decimal

from models import Anomaly, OrderItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds (could later live in a config table per-tenant)
# ---------------------------------------------------------------------------
MAX_REASONABLE_QUANTITY = 10_000


def detect_anomalies(
    order_id: uuid.UUID,
    order_items: list[OrderItem],
) -> list[Anomaly]:
    """Run rule-based anomaly checks against a set of order items.

    Returns a list of *transient* Anomaly ORM objects (not yet flushed).
    """
    anomalies: list[Anomaly] = []

    for item in order_items:
        # Rule 1 — Unusual volume
        if item.quantity > MAX_REASONABLE_QUANTITY:
            logger.warning(
                "Anomaly: item %s has quantity %d (> %d)",
                item.product_id,
                item.quantity,
                MAX_REASONABLE_QUANTITY,
            )
            anomalies.append(
                Anomaly(
                    order_id=order_id,
                    rule_code="UNUSUAL_VOLUME",
                    description=(
                        f"Quantity {item.quantity} for product {item.product_id} "
                        f"exceeds threshold of {MAX_REASONABLE_QUANTITY}"
                    ),
                    severity_score=Decimal("8.00"),
                    is_resolved=False,
                )
            )

        # Rule 2 — Missing / zero price
        if item.unit_price is None or item.unit_price <= 0:
            logger.warning(
                "Anomaly: item %s has zero/missing price", item.product_id
            )
            anomalies.append(
                Anomaly(
                    order_id=order_id,
                    rule_code="ZERO_PRICE",
                    description=(
                        f"Unit price is {item.unit_price} for product {item.product_id}"
                    ),
                    severity_score=Decimal("6.50"),
                    is_resolved=False,
                )
            )

    return anomalies
