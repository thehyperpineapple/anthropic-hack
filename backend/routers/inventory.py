from fastapi import APIRouter
from sqlalchemy import select

from dependencies import DBSession
from models import Inventory
from schemas import InventoryRead

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryRead])
async def list_inventory(session: DBSession) -> list[Inventory]:
    """List all inventory items."""
    result = await session.execute(
        select(Inventory).order_by(Inventory.product_name)
    )
    return list(result.scalars().all())
