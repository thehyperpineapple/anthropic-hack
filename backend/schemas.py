from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models import InteractionStatus, OrderStatus, SourceType


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------

class TenantBase(BaseModel):
    name: str


class TenantCreate(TenantBase):
    pass


class TenantRead(TenantBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str


class UserCreate(UserBase):
    tenant_id: UUID


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class CustomerCreate(CustomerBase):
    tenant_id: UUID


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductBase(BaseModel):
    name: str
    sku: str
    price: Decimal = Field(ge=0)


class ProductCreate(ProductBase):
    tenant_id: UUID


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Interaction
# ---------------------------------------------------------------------------

class InteractionBase(BaseModel):
    customer_id: UUID
    source_type: SourceType
    external_reference_id: Optional[str] = None
    raw_asset_url: Optional[str] = None


class InteractionCreate(InteractionBase):
    tenant_id: UUID
    status: InteractionStatus = InteractionStatus.PENDING


class InteractionRead(InteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: InteractionStatus
    created_at: datetime


# ---------------------------------------------------------------------------
# AI Analysis Log
# ---------------------------------------------------------------------------

class AIAnalysisLogBase(BaseModel):
    interaction_id: UUID
    transcript_text: Optional[str] = None
    raw_extraction_json: Optional[Any] = None
    confidence_score: Optional[Decimal] = Field(default=None, ge=0, le=1)


class AIAnalysisLogCreate(AIAnalysisLogBase):
    pass


class AIAnalysisLogRead(AIAnalysisLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class OrderBase(BaseModel):
    customer_id: UUID
    interaction_id: Optional[UUID] = None


class OrderCreate(OrderBase):
    tenant_id: UUID
    status: OrderStatus = OrderStatus.DRAFT
    total_amount: Decimal = Decimal("0")


class OrderRead(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    customer_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Order Item
# ---------------------------------------------------------------------------

class OrderItemBase(BaseModel):
    order_id: UUID
    product_id: UUID
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: Optional[str] = None
    product_sku: Optional[str] = None


# ---------------------------------------------------------------------------
# Quote
# ---------------------------------------------------------------------------

class QuoteBase(BaseModel):
    order_id: UUID
    quote_amount: Decimal = Field(ge=0)
    valid_until: Optional[date] = None


class QuoteCreate(QuoteBase):
    pass


class QuoteRead(QuoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Anomaly
# ---------------------------------------------------------------------------

class AnomalyBase(BaseModel):
    order_id: UUID
    rule_code: str
    description: Optional[str] = None
    severity_score: Optional[Decimal] = Field(default=None, ge=0)


class AnomalyCreate(AnomalyBase):
    is_resolved: bool = False


class AnomalyRead(AnomalyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_resolved: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Composite / Response schemas
# ---------------------------------------------------------------------------

class OrderDetailRead(OrderRead):
    """Full order view returned by GET /orders/{id}."""

    items: list[OrderItemRead] = []
    anomalies: list[AnomalyRead] = []
    quotes: list[QuoteRead] = []


class InteractionTextRequest(BaseModel):
    """Accept pre-transcribed text (transcription done on frontend)."""
    transcript: str
    source_type: SourceType
    customer_id: UUID


class InteractionUploadResponse(BaseModel):
    interaction_id: UUID
    order_id: UUID
    status: str
    anomalies_detected: int


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class OrdersByStatus(BaseModel):
    DRAFT: int = 0
    FLAGGED: int = 0
    CONFIRMED: int = 0
    SYNCED: int = 0


class AnalyticsSummary(BaseModel):
    total_orders: int
    total_revenue: str
    avg_order_value: str
    orders_by_status: OrdersByStatus
    error_count: int


class TopProduct(BaseModel):
    product_id: UUID
    product_name: str
    sku: str
    total_qty: int
    total_revenue: str


class RevenueOverTime(BaseModel):
    period: str
    revenue: str
    order_count: int
