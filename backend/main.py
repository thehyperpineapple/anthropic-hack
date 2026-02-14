import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from config import settings, validate_settings
from routers import analytics, customers, inventory, orders

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

validate_settings()

app = FastAPI(
    title="OrderFlow AI",
    version="0.2.0",
    description="AI-driven order entry from voice and text interactions.",
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
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(analytics.router)
app.include_router(inventory.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
