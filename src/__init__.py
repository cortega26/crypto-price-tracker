"""
Crypto Price Tracker

A comprehensive package for real-time cryptocurrency price tracking, alert management,
and automated notifications.

Features:
- Real-time price tracking for multiple cryptocurrencies via Binance WebSocket API
- Customizable price alerts for all-time highs, all-time lows, and specific thresholds
- Historical price data analysis and trend identification
- Email notifications for triggered alerts and daily price digests
- Configurable settings for alert thresholds, notification frequency, and tracked symbols
- Robust error handling and automatic reconnection for WebSocket streams
- Extensible architecture allowing easy addition of new data sources or notification methods

This package is designed for cryptocurrency enthusiasts, traders, and developers
who need reliable, up-to-date price information and automated alerting. It can be
used as a standalone application or integrated into larger trading systems and
data analysis pipelines.

For detailed usage instructions and API documentation, please refer to the
README.md file and the package documentation.
"""

import logging
from typing import Tuple, Optional

from .config import Config, get_config
from .api_client import BinanceAPIClient
from .price_tracker import PriceTracker
from .notification import EmailNotificationHandler
from .alert_manager import AlertManager
from .websocket_handler import WebSocketHandler
from .main import CryptoPriceTracker, main
from .gui import PriceTrackerGUI

__all__: Tuple[str, ...] = (
    "Config",
    "get_config",
    "BinanceAPIClient",
    "PriceTracker",
    "EmailNotificationHandler",
    "AlertManager",
    "WebSocketHandler",
    "CryptoPriceTracker",
    "PriceTrackerGUI",
    "main",
)

__version__ = "1.0.0"
__author__ = "Carlos Ortega González"
__email__ = "carlosortega77@gmail.com"
__license__ = "Apache License 2.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())


def get_version() -> str:
    """Return the current version of the package."""
    return __version__


def setup_logger(level: Optional[int] = None) -> None:
    """
    Set up basic logging for the package.

    Args:
        level (Optional[int]): The logging level. Defaults to None.
    """
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def format_price(price: float, decimals: int = 2) -> str:
    """
    Format a price with a specified number of decimal places.

    Args:
        price (float): The price to format.
        decimals (int): The number of decimal places to show. Defaults to 2.

    Returns:
        str: The formatted price as a string.
    """
    return f"{price:.{decimals}f}"


if __name__ == "__main__":
    print(f"Crypto Price Tracker version {get_version()}")
    print("Licensed under the Apache License, Version 2.0")
    print("Example usage:")
    print("from src import CryptoPriceTracker, get_config")
    print("config = get_config()")
    print("tracker = CryptoPriceTracker(config)")
    print("tracker.run()")
