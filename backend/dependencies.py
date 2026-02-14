import uuid
from typing import Annotated, AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_current_tenant(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> uuid.UUID:
    if x_tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Tenant-ID header",
        )
    try:
        return uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Tenant-ID is not a valid UUID",
        )


DBSession = Annotated[AsyncSession, Depends(get_db)]
TenantID = Annotated[uuid.UUID, Depends(get_current_tenant)]
