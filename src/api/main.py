"""FastAPI application for BTC Grid Bot."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import configs, health

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
app.include_router(health.router, tags=["Health"])
app.include_router(configs.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BTC Grid Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
