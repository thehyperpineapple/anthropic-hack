"""Seed the database with sample customers and inventory.

Usage:
    python seed.py
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select, text

from database import async_session_factory, engine, Base
from models import Customer, Inventory


CUSTOMERS = [
    {
        "company_name": "Acme Manufacturing",
        "contact_name": "John Mitchell",
        "email": "orders@acme-mfg.com",
        "phone": "+1 (415) 555-0142",
        "payment_terms": "Net-30",
        "shipping_preference": "Standard",
        "notes": "VIP customer, high volume buyer",
    },
    {
        "company_name": "BuildCo",
        "contact_name": "Sarah Chen",
        "email": "procurement@buildco.io",
        "phone": "+1 (415) 555-0198",
        "payment_terms": "Net-60",
        "shipping_preference": "Express",
        "notes": "Construction company, bulk steel orders",
    },
    {
        "company_name": "TechParts Inc",
        "contact_name": "Alex Rivera",
        "email": "hello@techparts.co",
        "phone": "+1 (650) 555-0177",
        "payment_terms": "Net-30",
        "shipping_preference": "Standard",
    },
    {
        "company_name": "Global Widgets",
        "contact_name": "Maria Thompson",
        "email": "orders@globalwidgets.com",
        "phone": "+1 (212) 555-0134",
        "payment_terms": "Net-30",
        "shipping_preference": "Standard",
        "notes": "Retail distribution, regular reorders",
    },
    {
        "company_name": "MegaCorp",
        "contact_name": "David Park",
        "email": "supply@megacorp.com",
        "phone": "+1 (310) 555-0156",
        "payment_terms": "Net-45",
        "shipping_preference": "Express",
        "notes": "Enterprise client, R&D procurement",
    },
]

INVENTORY = [
    {
        "sku": "WIDGET-001",
        "product_name": "Blue Widget",
        "description": "Standard blue widget, industrial grade",
        "category": "Widgets",
        "unit_price": Decimal("15.50"),
        "quantity_in_stock": 10000,
        "reorder_point": 500,
        "reorder_quantity": 2000,
        "supplier_name": "Widget Corp",
        "cost_per_unit": Decimal("8.25"),
    },
    {
        "sku": "WIDGET-002",
        "product_name": "Red Widget",
        "description": "Standard red widget, industrial grade",
        "category": "Widgets",
        "unit_price": Decimal("16.00"),
        "quantity_in_stock": 8000,
        "reorder_point": 400,
        "reorder_quantity": 1500,
        "supplier_name": "Widget Corp",
        "cost_per_unit": Decimal("8.50"),
    },
    {
        "sku": "WIDGET-003",
        "product_name": "Green Widget",
        "description": "Standard green widget, industrial grade",
        "category": "Widgets",
        "unit_price": Decimal("17.67"),
        "quantity_in_stock": 5000,
        "reorder_point": 300,
        "reorder_quantity": 1000,
        "supplier_name": "Widget Corp",
        "cost_per_unit": Decimal("9.00"),
    },
    {
        "sku": "GADGET-PRO",
        "product_name": "Gadget Pro",
        "description": "Premium gadget with advanced features",
        "category": "Gadgets",
        "unit_price": Decimal("23.50"),
        "quantity_in_stock": 5000,
        "reorder_point": 200,
        "reorder_quantity": 800,
        "supplier_name": "Gadget Works",
        "cost_per_unit": Decimal("12.00"),
    },
    {
        "sku": "STL-100",
        "product_name": "Steel Beam A",
        "description": "Standard I-beam, 6m length",
        "category": "Steel",
        "unit_price": Decimal("45.00"),
        "quantity_in_stock": 3000,
        "reorder_point": 100,
        "reorder_quantity": 500,
        "supplier_name": "SteelMax Industries",
        "cost_per_unit": Decimal("28.00"),
    },
    {
        "sku": "STL-200",
        "product_name": "Steel Beam B",
        "description": "Heavy-duty I-beam, 8m length",
        "category": "Steel",
        "unit_price": Decimal("52.00"),
        "quantity_in_stock": 2500,
        "reorder_point": 100,
        "reorder_quantity": 400,
        "supplier_name": "SteelMax Industries",
        "cost_per_unit": Decimal("32.00"),
    },
    {
        "sku": "BLT-050",
        "product_name": "Bolt Pack (100)",
        "description": "Industrial grade bolts, pack of 100",
        "category": "Fasteners",
        "unit_price": Decimal("8.50"),
        "quantity_in_stock": 20000,
        "reorder_point": 1000,
        "reorder_quantity": 5000,
        "supplier_name": "FastenerPro",
        "cost_per_unit": Decimal("4.25"),
    },
    {
        "sku": "NUT-050",
        "product_name": "Nut Pack (100)",
        "description": "Industrial grade nuts, pack of 100",
        "category": "Fasteners",
        "unit_price": Decimal("6.75"),
        "quantity_in_stock": 20000,
        "reorder_point": 1000,
        "reorder_quantity": 5000,
        "supplier_name": "FastenerPro",
        "cost_per_unit": Decimal("3.25"),
    },
    {
        "sku": "PCB-200",
        "product_name": "Circuit Board v2",
        "description": "Multi-layer PCB, standard footprint",
        "category": "Electronics",
        "unit_price": Decimal("52.00"),
        "quantity_in_stock": 4000,
        "reorder_point": 200,
        "reorder_quantity": 1000,
        "supplier_name": "CircuitTech",
        "cost_per_unit": Decimal("28.00"),
    },
    {
        "sku": "SNS-100",
        "product_name": "Sensor Module",
        "description": "Multi-sensor IoT module with WiFi",
        "category": "Electronics",
        "unit_price": Decimal("60.00"),
        "quantity_in_stock": 3000,
        "reorder_point": 150,
        "reorder_quantity": 500,
        "supplier_name": "SensorTech",
        "cost_per_unit": Decimal("35.00"),
    },
]


async def seed() -> None:
    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(select(Customer).limit(1))
        if result.scalar_one_or_none() is not None:
            print("Database already seeded. Skipping.")
            return

        # Seed customers
        for data in CUSTOMERS:
            session.add(Customer(**data))

        # Seed inventory
        for data in INVENTORY:
            session.add(Inventory(**data))

        await session.commit()
        print(f"Seeded {len(CUSTOMERS)} customers and {len(INVENTORY)} inventory items.")


async def main() -> None:
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
