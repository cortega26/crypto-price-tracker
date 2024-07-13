from typing import List
from datetime import datetime
from dataclasses import dataclass
import asyncio

from notification import NotificationHandler
from config import Config, get_config


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


class AlertManager:
    """
    Manages and sends alerts based on price events.

    This class is responsible for creating alerts, sending notifications,
    and maintaining a record of significant events for daily digests.
    """

    def __init__(self, notification_handler: NotificationHandler, config: Config):
        """
        Initialize the AlertManager.

        Args:
            notification_handler (NotificationHandler): Handler for sending notifications.
            config (Config): Configuration object containing settings.
        """
        self.notification_handler = notification_handler
        self.config = config
        self.ath_events: List[PriceEvent] = []
        self.atl_events: List[PriceEvent] = []
        self.ninety_day_ath_events: List[PriceEvent] = []
        self.ninety_day_atl_events: List[PriceEvent] = []
        self.price_movement_events: List[PriceEvent] = []

    async def send_alert(
        self, alert_type: str, symbol: str, price: float, additional_info: str = ""
    ) -> None:
        """
        Send an alert for a significant price event.

        This method creates an alert, sends a notification, and records the event for the daily digest.

        Args:
            alert_type (str): The type of alert (e.g., 'ATH', 'ATL', 'Price Movement').
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
            price (float): The current price that triggered the alert.
            additional_info (str, optional): Any additional information to include in the alert.

        Raises:
            Exception: If there's an error sending the notification.
        """
        subject = f"{alert_type} Alert: {symbol}"
        body = f"The coin {symbol} has triggered a {alert_type} alert at price {price}. {additional_info}"

        try:
            await asyncio.create_task(
                self.notification_handler.send_notification(subject, body)
            )
        except Exception as e:
            print(f"Error sending notification: {e}")
            raise

        event = PriceEvent(
            symbol=symbol,
            price=price,
            time=datetime.now().isoformat(),
            event_type=alert_type,
        )
        self._record_event(event)

    def _record_event(self, event: PriceEvent) -> None:
        """
        Record a price event for inclusion in the daily digest.

        Args:
            event (PriceEvent): The price event to record.
        """
        event_type_mapping = {
            "ATH": self.ath_events,
            "ATL": self.atl_events,
            "90-Day ATH": self.ninety_day_ath_events,
            "90-Day ATL": self.ninety_day_atl_events,
            "Price Movement": self.price_movement_events,
        }
        event_list = event_type_mapping.get(event.event_type)
        if event_list:
            event_list.append(event)

    async def send_daily_digest(self) -> None:
        """
        Send a daily digest of all recorded price events.

        This method compiles all recorded events into a summary and sends it as a notification.
        After sending, it clears all recorded events.

        Raises:
            Exception: If there's an error sending the notification.
        """
        now = datetime.now()
        subject = f"Daily Digest for {now.strftime('%Y-%m-%d')}"
        body = self._compile_digest_body()

        try:
            await self.notification_handler.send_notification(subject, body)
        except Exception as e:
            print(f"Error sending daily digest: {e}")
            raise
        finally:
            self._clear_recorded_events()

    def _compile_digest_body(self) -> str:
        """
        Compile the body of the daily digest from recorded events.

        Returns:
            str: The compiled body of the daily digest.
        """
        body = "Daily Digest\n\n"

        for event_list, event_type in [
            (self.ath_events, "All-Time Highs"),
            (self.atl_events, "All-Time Lows"),
            (self.ninety_day_ath_events, "90-Day Highs"),
            (self.ninety_day_atl_events, "90-Day Lows"),
            (self.price_movement_events, "Significant Price Movements"),
        ]:
            if event_list:
                body += f"{event_type}:\n"
                for event in event_list:
                    body += f"Symbol: {event.symbol}, Price: {event.price}, Time: {event.time}\n"
                body += "\n"

        if body == "Daily Digest\n\n":
            body += "No significant events occurred in the past 24 hours."

        return body

    def _clear_recorded_events(self) -> None:
        """
        Clear all recorded events after sending the daily digest.
        """
        self.ath_events.clear()
        self.atl_events.clear()
        self.ninety_day_ath_events.clear()
        self.ninety_day_atl_events.clear()
        self.price_movement_events.clear()


# Example usage
if __name__ == "__main__":
    import asyncio
    from notification import EmailNotificationHandler

    async def test_alert_manager():
        config = get_config()
        notification_handler = EmailNotificationHandler(config)
        alert_manager = AlertManager(notification_handler, config)

        # Simulate some alerts
        await alert_manager.send_alert("ATH", "BTCUSDT", 50000, "New all-time high!")
        await alert_manager.send_alert(
            "Price Movement", "ETHUSDT", 3000, "20% increase in the last hour"
        )

        # Send daily digest
        try:
            await alert_manager.send_daily_digest()
        except Exception as e:
            print(f"Error sending daily digest: {e}")

    try:
        asyncio.run(test_alert_manager())
    except Exception as e:
        print(f"Error during script execution: {e}")
