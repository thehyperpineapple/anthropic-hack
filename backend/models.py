from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Computed,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Customer(Base):
    __tablename__ = "customer_new"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(50), nullable=False, server_default="Net-30")
    shipping_preference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_since: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    total_lifetime_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    order_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Inventory(Base):
    __tablename__ = "inventory_new"

    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_in_stock: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    quantity_available: Mapped[int] = mapped_column(
        Integer,
        Computed("quantity_in_stock - quantity_reserved"),
        nullable=False,
    )
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    reorder_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="500")
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="14")
    supplier_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cost_per_unit: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    last_restocked: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Order(Base):
    __tablename__ = "orders_new"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_company_name: Mapped[str] = mapped_column(String(255), nullable=False)

    order_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")

    items: Mapped[list] = mapped_column(JSON, nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    estimated_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    order_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    original_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    quote_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quote_audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    quote_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    has_warnings: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    warnings: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
