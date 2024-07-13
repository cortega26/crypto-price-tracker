from abc import ABC, abstractmethod
from typing import Dict
import asyncio
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from cachetools import TTLCache

from config import get_config

config = get_config()
logger = logging.getLogger(__name__)


class APIClient(ABC):
    """
    Abstract base class for API clients.

    This class defines the interface for API clients used in the Crypto Price Tracker.
    Concrete implementations should inherit from this class and implement its methods.
    """

    @abstractmethod
    async def get_historical_data(self, symbol: str, limit: int = 1000) -> Dict:
        """
        Retrieve historical price data for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
            limit (int): The number of historical data points to retrieve. Defaults to 1000.

        Returns:
            Dict: A dictionary containing the symbol and its historical price data.
        """

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').

        Returns:
            float: The current price of the symbol.
        """

    @abstractmethod
    async def is_symbol_trading(self, symbol: str) -> bool:
        """
        Check if a given symbol is currently trading.

        Args:
            symbol (str): The trading symbol to check (e.g., 'BTCUSDT').

        Returns:
            bool: True if the symbol is trading, False otherwise.
        """


class BinanceAPIClient(APIClient):
    """
    Binance API client implementation.

    This class provides methods to interact with the Binance API for retrieving
    cryptocurrency price data and trading information.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize the Binance API client.

        Args:
            api_key (str): The Binance API key.
            api_secret (str): The Binance API secret.
        """
        self.client = Client(api_key, api_secret)
        self.historical_data_cache = TTLCache(
            maxsize=100, ttl=config.HISTORICAL_DATA_CACHE_TTL
        )

    async def get_historical_data(self, symbol: str, limit: int = 1000) -> Dict:
        """
        Retrieve historical price data for a given symbol from Binance.

        This method uses a cache to store recent requests and avoid unnecessary API calls.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
            limit (int): The number of historical data points to retrieve. Defaults to 1000.

        Returns:
            Dict: A dictionary containing the symbol and its historical price data.

        Raises:
            BinanceAPIException: If there's an error fetching data from Binance API.
        """
        cache_key = f"{symbol}_{limit}"
        if cache_key in self.historical_data_cache:
            return self.historical_data_cache[cache_key]

        try:
            klines = await asyncio.to_thread(
                self.client.futures_klines,
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_4HOUR,
                limit=limit,
            )
            result = {"symbol": symbol, "klines": klines}
            self.historical_data_cache[cache_key] = result
            return result
        except BinanceAPIException as e:
            logger.error(
                f"Error fetching historical data for {symbol}: {e.message} ({e.code})"
            )
            return {"symbol": symbol, "klines": []}

    async def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a given symbol from Binance.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').

        Returns:
            float: The current price of the symbol.

        Raises:
            BinanceAPIException: If there's an error fetching data from Binance API.
        """
        try:
            ticker_data = await asyncio.to_thread(
                self.client.futures_symbol_ticker, symbol=symbol
            )
            price = float(ticker_data.get("price", 0))
            return price
        except BinanceAPIException as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return 0.0

    async def is_symbol_trading(self, symbol: str) -> bool:
        """
        Check if a given symbol is currently trading on Binance.

        Args:
            symbol (str): The trading symbol to check (e.g., 'BTCUSDT').

        Returns:
            bool: True if the symbol is trading, False otherwise.

        Raises:
            BinanceAPIException: If there's an error fetching data from Binance API.
        """
        try:
            exchange_info = await asyncio.to_thread(self.client.futures_exchange_info)
            for symbol_info in exchange_info["symbols"]:
                if symbol_info["symbol"] == symbol:
                    return symbol_info["status"] == "TRADING"
            return False
        except BinanceAPIException as e:
            logger.error(f"Error checking if symbol {symbol} is trading: {e}")
            return False

    async def close(self):
        logger.info("Closing Binance API client...")
        try:
            if (
                hasattr(self.client, "_request_params")
                and "session" in self.client._request_params
            ):
                session = self.client._request_params["session"]
                if not session.closed:
                    await session.close()
                    logger.info("Closed aiohttp session")

            if hasattr(self.client, "_websocket_stop"):
                await self.client._websocket_stop()
                logger.info("Closed websocket connections")

        except Exception as e:
            logger.error(f"Error during Binance API client shutdown: {e}")
        finally:
            logger.info("Binance API client closed")


# Example usage
if __name__ == "__main__":
    async def test_api_client():
        client = BinanceAPIClient(config.API_KEY, config.API_SECRET)
        symbol = "BTCUSDT"

        historical_data = await client.get_historical_data(symbol)
        print(
            f"Historical data for {symbol}: {len(historical_data['klines'])} data points"
        )

        current_price = await client.get_current_price(symbol)
        print(f"Current price of {symbol}: {current_price}")

        is_trading = await client.is_symbol_trading(symbol)
        print(f"Is {symbol} trading: {is_trading}")

    asyncio.run(test_api_client())
