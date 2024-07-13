from typing import Dict, List, Optional, Union
import time
from dataclasses import dataclass
from api_client import APIClient
import asyncio


@dataclass
class PriceEvent:
    """
    Represents a significant price event for a cryptocurrency.

    Attributes:
        symbol (str): The trading symbol (e.g., 'BTCUSDT').
        price (float): The price at which the event occurred.
        time (str): The timestamp of the event in ISO format.
        event_type (str): The type of event (e.g., 'ATH', 'ATL', '90-Day High').
    """

    symbol: str
    price: float
    time: str
    event_type: str


class PriceTracker:
    """
    Tracks and analyzes cryptocurrency price movements.

    This class is responsible for maintaining price history, calculating price changes,
    and identifying significant price events such as all-time highs and lows.
    """

    def __init__(self, api_client: APIClient):
        """
        Initialize the PriceTracker.

        Args:
            api_client (APIClient): An instance of the API client used to fetch price data.
        """
        self.api_client = api_client
        self.all_time_highs: Dict[str, float] = {}
        self.all_time_lows: Dict[str, float] = {}
        self.ninety_day_highs: Dict[str, float] = {}
        self.ninety_day_lows: Dict[str, float] = {}
        self.price_changes: Dict[str, List[Dict[str, Union[float, int]]]] = {}

    async def update_price_change(
        self, symbol: str, current_price: float, timeframe: int = 3600
    ) -> Optional[float]:
        """
        Update the price change for a given symbol and calculate the percentage change.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
            current_price (float): The current price of the symbol.
            timeframe (int): The time frame in seconds to calculate the price change. Defaults to 3600 (1 hour).

        Returns:
            Optional[float]: The percentage price change over the specified timeframe, or None if insufficient data.
        """
        current_time = int(time.time())
        if symbol not in self.price_changes:
            self.price_changes[symbol] = []

        self.price_changes[symbol] = [
            entry
            for entry in self.price_changes[symbol]
            if current_time - entry["timestamp"] <= timeframe
        ]

        self.price_changes[symbol].append(
            {"price": current_price, "timestamp": current_time}
        )

        if len(self.price_changes[symbol]) > 1:
            initial_price = self.price_changes[symbol][0]["price"]
            price_change = (current_price - initial_price) / initial_price * 100
            return price_change

        return None

    async def update_all_time_high_low(self, symbol: str) -> None:
        """
        Update the all-time high and low prices for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
        """
        historical_data = await self.api_client.get_historical_data(symbol)
        if historical_data and historical_data["klines"]:
            klines = historical_data["klines"]
            self.all_time_highs[symbol] = max(float(kline[2]) for kline in klines)
            self.all_time_lows[symbol] = min(float(kline[3]) for kline in klines)

    async def update_ninety_day_high_low(self, symbol: str) -> None:
        """
        Update the 90-day high and low prices for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
        """
        historical_data = await self.api_client.get_historical_data(
            symbol, limit=540
        )  # 90 days * 6 4-hour candles per day
        if historical_data and historical_data["klines"]:
            klines = historical_data["klines"]
            self.ninety_day_highs[symbol] = max(float(kline[2]) for kline in klines)
            self.ninety_day_lows[symbol] = min(float(kline[3]) for kline in klines)

    async def get_all_time_high(self, symbol: str) -> Optional[float]:
        """
        Get the all-time high price for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').

        Returns:
            Optional[float]: The all-time high price, or None if not available.
        """
        if symbol not in self.all_time_highs:
            await self.update_all_time_high_low(symbol)
        return self.all_time_highs.get(symbol)

    async def get_all_time_low(self, symbol: str) -> Optional[float]:
        """
        Get the all-time low price for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').

        Returns:
            Optional[float]: The all-time low price, or None if not available.
        """
        if symbol not in self.all_time_lows:
            await self.update_all_time_high_low(symbol)
        return self.all_time_lows.get(symbol)

    async def get_ninety_day_high(self, symbol: str) -> Optional[float]:
        """
        Get the 90-day high price for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').

        Returns:
            Optional[float]: The 90-day high price, or None if not available.
        """
        if symbol not in self.ninety_day_highs:
            await self.update_ninety_day_high_low(symbol)
        return self.ninety_day_highs.get(symbol)

    async def get_ninety_day_low(self, symbol: str) -> Optional[float]:
        """
        Get the 90-day low price for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').

        Returns:
            Optional[float]: The 90-day low price, or None if not available.
        """
        if symbol not in self.ninety_day_lows:
            await self.update_ninety_day_high_low(symbol)
        return self.ninety_day_lows.get(symbol)


# Example usage
if __name__ == "__main__":
    import asyncio
    from api_client import BinanceAPIClient
    from config import get_config

    async def test_price_tracker():
        config = get_config()
        api_client = BinanceAPIClient(config.API_KEY, config.API_SECRET)
        price_tracker = PriceTracker(api_client)

        symbol = "BTCUSDT"
        current_price = await api_client.get_current_price(symbol)

        print(f"Current price of {symbol}: {current_price}")

        price_change = await price_tracker.update_price_change(symbol, current_price)
        if price_change is not None:
            print(f"Price change in the last hour: {price_change:.2f}%")

        ath = await price_tracker.get_all_time_high(symbol)
        atl = await price_tracker.get_all_time_low(symbol)
        print(f"All-time high of {symbol}: {ath}")
        print(f"All-time low of {symbol}: {atl}")

        ninety_day_high = await price_tracker.get_ninety_day_high(symbol)
        ninety_day_low = await price_tracker.get_ninety_day_low(symbol)
        print(f"90-day high of {symbol}: {ninety_day_high}")
        print(f"90-day low of {symbol}: {ninety_day_low}")

    asyncio.run(test_price_tracker())
