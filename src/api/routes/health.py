"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring.

    Returns:
        dict: Health status with service name and status.
    """
    return {
        "status": "healthy",
        "service": "btcbot-api",
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint.

    Checks if the service is ready to accept requests.
    This can be extended to check database connections, etc.

    Returns:
        dict: Readiness status.
    """
    # TODO: Add checks for:
    # - Database connection
    # - BingX API availability
    # - GridManager state
    return {
        "status": "ready",
        "service": "btcbot-api",
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check endpoint.

    Simple check that the service is running.

    Returns:
        dict: Liveness status.
    """
    return {
        "status": "alive",
        "service": "btcbot-api",
    }
