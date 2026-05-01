"""FastAPI entrypoint for the NHL Predictions API."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import dashboard, historical, predictions, tickets, refresh

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm caches on startup so first requests are fast."""
    logger.info("Warming caches...")
    try:
        dashboard.get_summary()
        dashboard.get_standings()
        dashboard.get_top_scorers()
        historical.get_seasons()
        historical.get_teams()
        # Warm the latest season standings
        seasons = historical.get_seasons()
        if seasons:
            latest = seasons[-1]
            historical.get_standings(latest)
            historical.get_scorers(latest)
            historical.get_playoffs(latest)
        logger.info("Cache warming complete")
    except Exception as e:
        logger.warning("Cache warming failed (non-fatal): %s", e)
    yield


app = FastAPI(title="NHL Predictions API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.environ.get("CORS_ORIGIN", ""),
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/dashboard")
app.include_router(historical.router, prefix="/api/historical")
app.include_router(predictions.router, prefix="/api/predictions")
app.include_router(tickets.router, prefix="/api/tickets")
app.include_router(refresh.router, prefix="/api/refresh")


@app.get("/api/health")
def health():
    return {"status": "ok"}
