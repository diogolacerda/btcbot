from typing import Annotated

from fastapi import Depends

from src.client.bingx_client import BingXClient
from src.grid.grid_manager import GridManager
from src.utils.logger import main_logger


# Placeholder for actual singletons/dependencies
# These will be initialized in main.py and set here
class Dependencies:
    grid_manager: GridManager | None = None
    bingx_client: BingXClient | None = None


def get_grid_manager() -> GridManager:
    if Dependencies.grid_manager is None:
        main_logger.error("GridManager dependency not initialized!")
        raise ValueError("GridManager not initialized")
    return Dependencies.grid_manager


def get_bingx_client() -> BingXClient:
    if Dependencies.bingx_client is None:
        main_logger.error("BingXClient dependency not initialized!")
        raise ValueError("BingXClient not initialized")
    return Dependencies.bingx_client


# Type hints for FastAPI dependency injection
AnnotatedGridManager = Annotated[GridManager, Depends(get_grid_manager)]
AnnotatedBingXClient = Annotated[BingXClient, Depends(get_bingx_client)]
