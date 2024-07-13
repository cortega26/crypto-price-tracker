import asyncio
import json
import logging
import time
from typing import Optional, List, Set
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

from config import Config, get_config
from price_tracker import PriceTracker
from api_client import APIClient
from alert_manager import AlertManager

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    Handles WebSocket connections for real-time price updates.

    This class manages the WebSocket connection to the Binance futures stream,
    processes incoming messages, and triggers price checks and notifications.
    """

    def __init__(
        self,
        price_tracker: PriceTracker,
        alert_manager: AlertManager,
        api_client: APIClient,
        symbols_of_interest: Optional[List[str]],
        config: Config,
    ):
        """
        Initialize the WebSocketHandler.

        Args:
            price_tracker (PriceTracker): Service for tracking and analyzing prices.
            alert_manager (AlertManager): Service for managing and sending alerts.
            api_client (APIClient): Client for API interactions.
            symbols_of_interest (Optional[List[str]]): List of symbols to track. If None, all USDT futures are tracked.
            config (Config): Configuration object containing settings.
        """
        self.price_tracker = price_tracker
        self.alert_manager = alert_manager
        self.api_client = api_client
        self.symbols_of_interest: Optional[Set[str]] = (
            set(symbols_of_interest) if symbols_of_interest else None
        )
        self.all_usdt_symbols: Set[str] = set()
        self.config = config
        self.last_message_time: Optional[float] = None
        self.connection_timeout: int = 600

    async def initialize_symbols(self) -> None:
        """
        Initialize the list of symbols to track.

        If no specific symbols are provided, this method fetches all available USDT futures symbols.
        """
        if self.symbols_of_interest is None:
            try:
                exchange_info = await asyncio.to_thread(
                    self.api_client.client.futures_exchange_info
                )
                self.all_usdt_symbols = {
                    symbol["symbol"]
                    for symbol in exchange_info["symbols"]
                    if symbol["symbol"].endswith("USDT")
                    and symbol["status"] == "TRADING"
                }
                logger.info(
                    f"Initialized with {len(self.all_usdt_symbols)} USDT futures symbols"
                )
            except Exception as e:
                logger.error(f"Error initializing USDT symbols: {e}")
                self.all_usdt_symbols = set()
        else:
            logger.info(
                f"Using specified symbols of interest: {self.symbols_of_interest}"
            )

    async def handle_websocket(
        self, websocket: websockets.WebSocketClientProtocol
    ) -> None:
        """
        Handle the WebSocket connection and process incoming messages.

        This method maintains the WebSocket connection, processes incoming messages,
        and triggers price checks for relevant symbols.

        Args:
            websocket (websockets.WebSocketClientProtocol): The WebSocket connection object.
        """
        await self.initialize_symbols()
        symbols_to_track = (
            self.symbols_of_interest
            if self.symbols_of_interest is not None
            else self.all_usdt_symbols
        )

        connection_check_task = asyncio.create_task(self.check_connection(websocket))

        try:
            async for message in websocket:
                self.last_message_time = time.time()

                if isinstance(message, bytes):
                    await websocket.pong(message)
                    logger.debug("Received ping, sent pong")
                    continue

                try:
                    data = json.loads(message)
                    await self.process_message(data, symbols_to_track)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON: {e}")
        except ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}. Reconnecting...")
        except InvalidStatusCode as e:
            logger.error(f"Invalid status code: {e.status_code}. Exiting...")
            raise
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
        finally:
            connection_check_task.cancel()
            try:
                await connection_check_task
            except asyncio.CancelledError:
                pass

    async def process_message(self, data: dict, symbols_to_track: Set[str]) -> None:
        """
        Process a message received from the WebSocket.

        This method extracts relevant price information from the message and
        triggers price checks for tracked symbols.

        Args:
            data (dict): The parsed JSON data from the WebSocket message.
            symbols_to_track (Set[str]): Set of symbols to track and process.
        """
        if isinstance(data, list):
            for ticker_data in data:
                symbol = ticker_data.get("s")
                if symbol in symbols_to_track:
                    current_price = float(ticker_data.get("p", 0))
                    if current_price > 0:
                        logger.info(
                            f"Received update for {symbol}: Price={current_price}"
                        )
                        await self.check_and_notify(symbol, current_price)
                    else:
                        logger.warning(
                            f"Received invalid price for {symbol}: {ticker_data.get('p')}"
                        )
        else:
            logger.error("Unexpected data format received from WebSocket.")

    async def check_and_notify(self, symbol: str, current_price: float) -> None:
        """
        Check price conditions and send notifications if necessary.

        This method coordinates between PriceTracker and AlertManager to check
        price conditions and send alerts when appropriate.

        Args:
            symbol (str): The trading symbol.
            current_price (float): The current price of the symbol.
        """
        price_change = await self.price_tracker.update_price_change(
            symbol, current_price
        )

        if (
            price_change is not None
            and abs(price_change) >= self.config.NOTIFICATION_THRESHOLD
        ):
            await self.alert_manager.send_alert(
                "Price Movement",
                symbol,
                current_price,
                f"Price changed by {price_change:.2f}% over the last {self.config.PERCENTAGE_CHANGE_TIMEFRAME} seconds",
            )

        ath = await self.price_tracker.get_all_time_high(symbol)
        atl = await self.price_tracker.get_all_time_low(symbol)
        ninety_day_high = await self.price_tracker.get_ninety_day_high(symbol)
        ninety_day_low = await self.price_tracker.get_ninety_day_low(symbol)

        if current_price > (ath or 0):
            await self.alert_manager.send_alert("ATH", symbol, current_price)
        elif current_price < (atl or float("inf")):
            await self.alert_manager.send_alert("ATL", symbol, current_price)
        elif current_price > (ninety_day_high or 0):
            await self.alert_manager.send_alert("90-Day ATH", symbol, current_price)
        elif current_price < (ninety_day_low or float("inf")):
            await self.alert_manager.send_alert("90-Day ATL", symbol, current_price)

    async def check_connection(
        self, websocket: websockets.WebSocketClientProtocol
    ) -> None:
        """
        Periodically check the WebSocket connection and close it if it appears to be dead.

        This method runs in the background to ensure the connection is alive and
        receiving messages regularly.

        Args:
            websocket (websockets.WebSocketClientProtocol): The WebSocket connection object to monitor.
        """
        await asyncio.sleep(self.connection_timeout)
        while True:
            if self.last_message_time is None:
                logger.debug("No messages received yet, continuing to wait...")
            elif time.time() - self.last_message_time > self.connection_timeout:
                logger.warning("Connection seems to be dead. Closing...")
                await websocket.close()
                break
            else:
                logger.debug(
                    f"Connection alive. Last message received {time.time() - self.last_message_time:.2f} seconds ago"
                )
            await asyncio.sleep(60)


# Example usage
if __name__ == "__main__":
    from api_client import BinanceAPIClient
    from notification import EmailNotificationHandler

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async def test_websocket_handler():
        config = get_config()
        logger.info("Config loaded successfully")

        api_client = BinanceAPIClient(config.API_KEY, config.API_SECRET)
        logger.info("BinanceAPIClient initialized")

        price_tracker = PriceTracker(api_client)
        logger.info("PriceTracker initialized")

        notification_handler = EmailNotificationHandler(config)
        logger.info("EmailNotificationHandler initialized")

        alert_manager = AlertManager(notification_handler, config)
        logger.info("AlertManager initialized")

        websocket_handler = WebSocketHandler(
            price_tracker,
            alert_manager,
            api_client,
            (
                config.SYMBOLS_OF_INTEREST.split(",")
                if config.SYMBOLS_OF_INTEREST
                else None
            ),
            config,
        )
        logger.info("WebSocketHandler initialized")

        uri = "wss://fstream.binance.com/ws/!markPrice@arr"
        logger.info(f"Attempting to connect to WebSocket at {uri}")

        try:
            async with websockets.connect(uri) as websocket:
                logger.info("WebSocket connection established")
                
                # Set a timeout for the WebSocket handler
                try:
                    await asyncio.wait_for(websocket_handler.handle_websocket(websocket), timeout=60)
                except asyncio.TimeoutError:
                    logger.warning("WebSocket handler timed out after 60 seconds")
                except ConnectionClosed as e:
                    logger.error(f"WebSocket connection closed unexpectedly: {e}")
                except Exception as e:
                    logger.error(f"An error occurred in the WebSocket handler: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}", exc_info=True)

    asyncio.run(test_websocket_handler())