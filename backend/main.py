import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings, validate_settings
from routers import interactions, orders

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
app.include_router(interactions.router)
app.include_router(orders.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
