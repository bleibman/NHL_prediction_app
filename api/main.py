"""FastAPI entrypoint for the NHL Predictions API."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import dashboard, historical, predictions, tickets, refresh

app = FastAPI(title="NHL Predictions API", version="1.0.0")

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
