import asyncio
import signal
import logging
from datetime import datetime, timedelta
import websockets
import sys
import threading
from websockets.exceptions import ConnectionClosed

from config import Config, get_config
from api_client import BinanceAPIClient
from price_tracker import PriceTracker
from notification import EmailNotificationHandler
from alert_manager import AlertManager
from websocket_handler import WebSocketHandler

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoPriceTracker:
    def __init__(self, config: Config):
        self.config = config
        self.api_client = BinanceAPIClient(config.API_KEY, config.API_SECRET)
        self.price_tracker = PriceTracker(self.api_client)
        self.notification_handler = EmailNotificationHandler(config)
        self.alert_manager = AlertManager(self.notification_handler, config)
        self.websocket_handler = WebSocketHandler(
            self.price_tracker,
            self.alert_manager,
            self.api_client,
            (
                config.SYMBOLS_OF_INTEREST.split(",")
                if config.SYMBOLS_OF_INTEREST
                else None
            ),
            config,
        )
        self.should_exit = threading.Event()

    async def run(self):
        try:
            digest_task = asyncio.create_task(self.schedule_daily_digest())

            uri = "wss://fstream.binance.com/ws/!markPrice@arr"
            retry_count = 0
            while not self.should_exit.is_set():
                try:
                    async with websockets.connect(uri) as websocket:
                        logger.info("WebSocket connection established.")
                        await self.websocket_handler.handle_websocket(websocket)
                        retry_count = 0
                except ConnectionClosed:
                    if self.should_exit.is_set():
                        break
                    logger.warning("WebSocket connection closed. Reconnecting...")
                except asyncio.CancelledError:
                    if self.should_exit.is_set():
                        break
                    logger.warning("WebSocket connection cancelled. Exiting...")
                except Exception as e:
                    if self.should_exit.is_set():
                        break
                    logger.error(f"WebSocket connection error: {e}")
                    retry_count += 1
                    if retry_count > self.config.MAX_RETRIES:
                        logger.error("Max retries reached. Exiting...")
                        break
                    wait_time = min(
                        self.config.INITIAL_RETRY_DELAY * (2**retry_count),
                        self.config.MAX_RETRY_DELAY,
                    )
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

            digest_task.cancel()
            try:
                await digest_task
            except asyncio.CancelledError:
                pass

        finally:
            await self.shutdown()

    def signal_handler(self):
        logger.info("Received termination signal. Initiating shutdown...")
        self.should_exit.set()

    async def schedule_daily_digest(self):
        while not self.should_exit.is_set():
            now = datetime.now()
            digest_time = datetime.strptime(
                self.config.DAILY_DIGEST_TIME, "%H:%M"
            ).time()
            next_run = datetime.combine(now.date(), digest_time)
            if now.time() > digest_time:
                next_run += timedelta(days=1)
            wait_seconds = (next_run - now).total_seconds()
            try:
                await asyncio.sleep(wait_seconds)
                if not self.should_exit.is_set():
                    await self.alert_manager.send_daily_digest()
            except asyncio.CancelledError:
                break

    async def shutdown(self):
        logger.info("Shutting down...")
        await self.api_client.close()
        await self.notification_handler.close()
        logger.info("Cleanup completed.")
        logger.info("Shutdown complete.")


def main():
    config = get_config()
    tracker = CryptoPriceTracker(config)

    logger.info("Starting Crypto Price Tracker...")

    if sys.platform.startswith("win"):
        # On Windows, use ProactorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        tracker.signal_handler()
        loop.call_soon_threadsafe(lambda: asyncio.create_task(shutdown(loop, tracker)))

    async def shutdown(loop, tracker):
        logger.info("Shutting down asyncio tasks...")
        tasks = [
            t for t in asyncio.all_tasks(loop=loop) if t is not asyncio.current_task()
        ]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await tracker.shutdown()
        loop.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        loop.run_until_complete(tracker.run())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logger.info("Event loop closed.")


if __name__ == "__main__":
    main()
