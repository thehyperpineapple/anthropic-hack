from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    payment_terms: str = "Net-30"
    shipping_preference: Optional[str] = None
    order_count: int = 0
    total_lifetime_value: Decimal = Decimal("0.00")


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inventory_id: int
    sku: str
    product_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Decimal
    quantity_in_stock: int = 0
    quantity_reserved: int = 0
    quantity_available: int = 0
    reorder_point: int = 100


# ---------------------------------------------------------------------------
# Order Items (JSONB shape)
# ---------------------------------------------------------------------------

class OrderItemSchema(BaseModel):
    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


# ---------------------------------------------------------------------------
# Order Warning (JSONB shape)
# ---------------------------------------------------------------------------

class OrderWarning(BaseModel):
    type: str
    message: str
    severity: str = "medium"


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    order_number: str
    customer_id: Optional[int] = None
    customer_company_name: str
    order_date: datetime
    status: str
    items: list[dict]
    subtotal: Decimal
    tax: Decimal = Decimal("0.00")
    shipping_cost: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    total_amount: Decimal
    order_source: Optional[str] = None
    ai_confidence_score: Optional[Decimal] = None
    has_warnings: bool = False
    created_at: datetime
    customer_name: Optional[str] = None


class OrderDetailRead(OrderRead):
    original_message: Optional[str] = None
    quote_text: Optional[str] = None
    quote_audio_url: Optional[str] = None
    warnings: Optional[list[dict]] = None
    estimated_delivery_date: Optional[date] = None
    shipping_method: Optional[str] = None
    requires_human_review: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Process Order Request / Response
# ---------------------------------------------------------------------------

class ProcessOrderRequest(BaseModel):
    customer_id: int
    source_type: str = Field(pattern=r"^(voice_message|text_file)$")
    original_message: str = Field(min_length=1)


class ProcessOrderResponse(BaseModel):
    order_id: int
    order_number: str
    customer_company_name: str
    status: str
    items: list[dict]
    subtotal: Decimal
    tax: Decimal = Decimal("0.00")
    total_amount: Decimal
    has_warnings: bool = False
    warnings: list[dict] = []
    requires_human_review: bool = False
    ai_confidence_score: Optional[Decimal] = None
    order_date: datetime


# ---------------------------------------------------------------------------
# Update Order Status
# ---------------------------------------------------------------------------

class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(pattern=r"^(pending|processing|completed|review_needed|error|cancelled)$")
    reviewed_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class AnalyticsSummary(BaseModel):
    total_orders: int
    total_revenue: Decimal
    avg_order_value: Decimal
    orders_by_status: dict[str, int]
    error_count: int


class TopProduct(BaseModel):
    sku: str
    product_name: str
    total_qty: int
    total_revenue: Decimal
