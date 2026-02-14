import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from config import settings, validate_settings
from database import Base, engine
from routers import analytics, customers, interactions, orders, products, tenants

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

validate_settings()

app = FastAPI(
    title="OrderFlow AI",
    version="0.1.0",
    description="AI-driven order entry from voice, email, and PDF interactions.",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins during development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(tenants.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(interactions.router)
app.include_router(orders.router)
app.include_router(analytics.router)


# ---------------------------------------------------------------------------
# Startup — ensure tables exist
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        def _tables_exist(sync_conn):
            inspector = inspect(sync_conn)
            existing = set(inspector.get_table_names())
            required = set(Base.metadata.tables.keys())
            return required.issubset(existing)

        already_created = await conn.run_sync(_tables_exist)

    if already_created:
        logger.info("All tables already exist — skipping creation")
        return

    logger.info("Creating missing tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
