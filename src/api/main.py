"""FastAPI application for BTC Grid Bot."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, configs, filters, health, trading_data

app = FastAPI(
    title="BTC Grid Bot API",
    description="REST API for BTC Grid Bot - Grid Trading System for BingX",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(health.router, tags=["Health"])
app.include_router(configs.router)
app.include_router(filters.router, tags=["Filters"])
app.include_router(trading_data.router, tags=["Trading Data"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BTC Grid Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
