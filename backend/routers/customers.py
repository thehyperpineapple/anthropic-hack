from fastapi import APIRouter
from sqlalchemy import select

from dependencies import DBSession
from models import Customer
from schemas import CustomerRead

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
async def list_customers(session: DBSession) -> list[Customer]:
    """List all customers."""
    result = await session.execute(
        select(Customer).order_by(Customer.company_name)
    )
    return list(result.scalars().all())
