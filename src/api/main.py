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
from src.utils.logger import api_logger as logger

# Global price streamer instance
_price_streamer = None

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
app.include_router(strategy.router)
app.include_router(orders.router)
app.include_router(trading_data.router, tags=["Trading Data"])
app.include_router(market_data.router)
app.include_router(metrics.router, tags=["Metrics"])
app.include_router(activity.router)

# WebSocket endpoint for real-time dashboard updates
app.include_router(dashboard_ws.router, tags=["WebSocket"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on API startup."""
    global _price_streamer

    try:
        from config import load_config
        from src.api.services.price_streamer import PriceStreamer

        config = load_config()
        _price_streamer = PriceStreamer(config.bingx, symbol=config.trading.symbol)
        await _price_streamer.start()
        logger.info("PriceStreamer started for real-time dashboard updates")
    except Exception as e:
        logger.error(f"Failed to start PriceStreamer: {e}")
        # Don't fail API startup if price streamer fails
        _price_streamer = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on API shutdown."""
    global _price_streamer

    if _price_streamer:
        try:
            await _price_streamer.stop()
            logger.info("PriceStreamer stopped")
        except Exception as e:
            logger.error(f"Error stopping PriceStreamer: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BTC Grid Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
