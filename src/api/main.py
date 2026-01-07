"""FastAPI application for BTC Grid Bot."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    activity,
    auth,
    bot_control,
    configs,
    filters,
    health,
    market_data,
    metrics,
    orders,
    strategy,
    trading_data,
)
from src.api.websocket import dashboard_ws

# Load CORS origins from environment variable
# Default to localhost:3000 if not set
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_ENV.split(",")]

app = FastAPI(
    title="BTC Grid Bot API",
    description="REST API for BTC Grid Bot - Grid Trading System for BingX",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for Web UI
# Origins are loaded from CORS_ORIGINS environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(health.router, tags=["Health"])
app.include_router(bot_control.router, tags=["Bot Control"])
app.include_router(configs.router)
app.include_router(strategy.router)
app.include_router(filters.router, tags=["Filters"])
app.include_router(orders.router)
app.include_router(trading_data.router, tags=["Trading Data"])
app.include_router(market_data.router)
app.include_router(metrics.router, tags=["Metrics"])
app.include_router(activity.router)

# WebSocket endpoint for real-time dashboard updates
app.include_router(dashboard_ws.router, tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BTC Grid Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
