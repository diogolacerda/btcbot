import logging
import os
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Setup a logger with console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


trades_logger = setup_logger("trades", "trades.log")
orders_logger = setup_logger("orders", "orders.log")
macd_logger = setup_logger("macd", "macd.log")
error_logger = setup_logger("errors", "errors.log")
main_logger = setup_logger("main", "main.log")
