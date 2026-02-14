import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import anthropic
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Customer, Inventory, Order

logger = logging.getLogger(__name__)


ORDER_EXTRACTION_PROMPT = """You are an order-parsing assistant for a B2B distribution company.

Given a customer's message (which may be a transcribed voice message or text),
extract the items they want to order.

Here is the current product catalog (SKU | Product Name | Unit Price):
{inventory_list}

INSTRUCTIONS:
- Match the customer's requested products to items in the catalog above.
- If the customer uses informal names (e.g. "blue widgets"), match to the closest catalog item.
- If a product cannot be matched to any catalog item, use sku "UNKNOWN" and include the original name.
- Extract the quantity for each item. If unclear, default to 1.

Return ONLY a valid JSON array. Each element must have exactly these keys:
  - "sku": string — the matched SKU from the catalog
  - "product_name": string — the matched product name from the catalog
  - "quantity": integer — the quantity requested

Example output:
[
  {{"sku": "WIDGET-001", "product_name": "Blue Widget", "quantity": 500}},
  {{"sku": "GADGET-PRO", "product_name": "Gadget Pro", "quantity": 200}}
]

Do NOT include any explanation, markdown fences, or extra keys.
Return ONLY the JSON array.
"""


class OrderProcessor:
    """Processes incoming order messages: Claude parsing + DB operations."""

    def __init__(self) -> None:
        self.anthropic_client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
        )

    async def process_order(
        self,
        *,
        customer_id: int,
        source_type: str,
        original_message: str,
        session: AsyncSession,
    ) -> dict[str, Any]:
        """End-to-end: parse message -> resolve inventory -> create order -> return result."""

        # 1. Look up customer
        result = await session.execute(
            select(Customer).where(Customer.customer_id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if customer is None:
            raise ValueError(f"Customer {customer_id} not found")

        # 2. Load inventory catalog for Claude context
        inv_result = await session.execute(select(Inventory))
        inventory_items = list(inv_result.scalars().all())

        inventory_list = "\n".join(
            f"{item.sku} | {item.product_name} | ${item.unit_price}"
            for item in inventory_items
        )

        # 3. Call Claude to parse the message
        prompt = ORDER_EXTRACTION_PROMPT.format(inventory_list=inventory_list)

        extracted_items = await asyncio.to_thread(
            self._call_claude, prompt, original_message
        )

        # 4. Resolve items against inventory and compute prices
        inv_map: dict[str, Inventory] = {item.sku: item for item in inventory_items}

        order_items: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        subtotal = Decimal("0")

        for raw in extracted_items:
            sku = raw.get("sku", "UNKNOWN")
            quantity = int(raw.get("quantity", 1))
            product_name = raw.get("product_name", sku)

            inv = inv_map.get(sku)
            if inv is None:
                warnings.append({
                    "type": "unknown_sku",
                    "message": f"Product '{product_name}' (SKU: {sku}) not found in catalog",
                    "severity": "high",
                })
                continue

            unit_price = inv.unit_price
            line_total = unit_price * quantity

            # Check stock availability
            if quantity > inv.quantity_available:
                warnings.append({
                    "type": "low_stock",
                    "message": f"{inv.product_name}: requested {quantity}, only {inv.quantity_available} available",
                    "severity": "medium",
                })

            # Check unusual volume
            if quantity > 1000:
                warnings.append({
                    "type": "high_quantity",
                    "message": f"{inv.product_name}: unusually large quantity ({quantity} units)",
                    "severity": "medium",
                })

            order_items.append({
                "sku": sku,
                "product_name": inv.product_name,
                "quantity": quantity,
                "unit_price": float(unit_price),
                "line_total": float(line_total),
            })
            subtotal += line_total

        if not order_items:
            warnings.append({
                "type": "no_items",
                "message": "No valid items could be extracted from the message",
                "severity": "high",
            })

        # 5. Generate order number
        count_result = await session.execute(
            text("SELECT COUNT(*) FROM orders_new")
        )
        count = count_result.scalar() or 0
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}{count + 1:02d}"

        # 6. Determine status
        has_warnings = len(warnings) > 0
        requires_review = any(w["severity"] == "high" for w in warnings)
        status = "review_needed" if requires_review else "pending"

        # 7. Create order
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            customer_company_name=customer.company_name,
            status=status,
            items=order_items,
            subtotal=subtotal,
            total_amount=subtotal,
            order_source=source_type,
            original_message=original_message,
            ai_confidence_score=Decimal("95.00") if not has_warnings else Decimal("70.00"),
            has_warnings=has_warnings,
            warnings=warnings if warnings else None,
            requires_human_review=requires_review,
        )
        session.add(order)
        await session.flush()

        # 8. Update inventory reservations
        for item in order_items:
            inv = inv_map.get(item["sku"])
            if inv:
                inv.quantity_reserved = inv.quantity_reserved + item["quantity"]

        # 9. Update customer stats
        customer.order_count = customer.order_count + 1
        customer.total_lifetime_value = customer.total_lifetime_value + subtotal

        await session.commit()

        logger.info(
            "Order %s created for %s: %d items, $%.2f, status=%s",
            order_number,
            customer.company_name,
            len(order_items),
            subtotal,
            status,
        )

        return {
            "order_id": order.order_id,
            "order_number": order.order_number,
            "customer_company_name": customer.company_name,
            "status": status,
            "items": order_items,
            "subtotal": float(subtotal),
            "tax": 0.00,
            "total_amount": float(subtotal),
            "has_warnings": has_warnings,
            "warnings": warnings,
            "requires_human_review": requires_review,
            "ai_confidence_score": 95.00 if not has_warnings else 70.00,
            "order_date": order.order_date.isoformat() if order.order_date else datetime.now().isoformat(),
        }

    def _call_claude(self, system_prompt: str, user_message: str) -> list[dict[str, Any]]:
        """Synchronous Claude call (run in thread)."""
        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text
        # Strip markdown fences if Claude adds them despite instructions
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        items: list[dict[str, Any]] = json.loads(cleaned)
        logger.info("Claude extracted %d items", len(items))
        return items
