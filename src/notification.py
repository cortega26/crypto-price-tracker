from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import time
import logging
import aiosmtplib
import asyncio
import keyring
import ssl

from config import Config, get_config

config = get_config()
logger = logging.getLogger(__name__)

APP_NAME = "CryptoPriceTracker"

class NotificationHandler(ABC):
    """
    Abstract base class for notification handlers.

    This class defines the interface for sending notifications in the Crypto Price Tracker.
    Concrete implementations should inherit from this class and implement its methods.
    """

    @abstractmethod
    async def send_notification(self, subject: str, body: str) -> None:
        """
        Send a notification.

        Args:
            subject (str): The subject of the notification.
            body (str): The body content of the notification.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """

class EmailNotificationHandler(NotificationHandler):
    def __init__(self, email_config: Config):
        self.email_config = email_config
        self.last_notification_time: Dict[str, float] = {}
        self.secondary_email_host = "smtp.secondary.com"
        self.secondary_email_port = 587
        self.smtp_client = None

        logger.debug(f"Email Host: {self.email_config.EMAIL_HOST}")
        logger.debug(f"Email Port: {self.email_config.EMAIL_PORT}")
        logger.debug(f"Email Address: {self.email_config.EMAIL_ADDRESS}")

        email_password = keyring.get_password(APP_NAME, "EMAIL_PASSWORD")
        logger.debug(f"Email Password retrieved from keyring: {'Yes' if email_password else 'No'}")

    async def send_notification(self, subject: str, body: str) -> None:
        """
        Handles email notifications including creation, sending, retries, and closing connections.

        Args:
            subject (str): The subject of the email notification.
            body (str): The body content of the email notification.

        Raises:
            Exception: If an error occurs during the email sending process.
        """
        current_time = time.time()
        if (
            subject in self.last_notification_time
            and current_time - self.last_notification_time[subject]
            < self.email_config.NOTIFICATION_INTERVAL
        ):
            logger.info(f"Skipping notification for {subject} due to rate limiting")
            return

        msg = self._create_email_message(subject, body)

        for attempt in range(self.email_config.MAX_RETRIES):
            try:
                await self._send_email(msg)
                logger.info(f"Sent email notification: {subject}")
                self.last_notification_time[subject] = current_time
                return
            except Exception as e:
                logger.error(f"Error sending email notification: {e}")
                if attempt < self.email_config.MAX_RETRIES - 1:
                    await self._handle_retry(attempt)
                else:
                    logger.error(
                        "Max retries reached for sending email. Trying secondary email server."
                    )
                    await self._send_via_secondary_server(msg)

    def _create_email_message(self, subject: str, body: str) -> MIMEMultipart:
        """
        Create an email message.

        Args:
            subject (str): The subject of the email.
            body (str): The body content of the email.

        Returns:
            MIMEMultipart: The created email message.
        """
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = self.email_config.EMAIL_ADDRESS
        msg["To"] = ", ".join(self.email_config.get_email_recipients())
        msg.attach(MIMEText(body, "plain"))
        return msg

    async def _send_email(self, msg: MIMEMultipart) -> None:
        """
        Sends an email message with the provided subject, body, and recipients.

        Args:
            msg (MIMEMultipart): The MIME message to be sent.

        Raises:
            ValueError: If the email password is not set in the keyring.
            aiosmtplib.SMTPException: If there is an SMTP-related error.
            ssl.SSLError: If there is an SSL-related error.
            Exception: If there is an unexpected error sending the email.
        """
        logger.debug("Attempting to send email...")
        context = ssl.create_default_context()
        
        email_password = keyring.get_password(APP_NAME, "EMAIL_PASSWORD")
        if not email_password:
            logger.error("Email password is not set in keyring")
            raise ValueError("Email password is not set in keyring")

        try:
            async with aiosmtplib.SMTP(hostname=self.email_config.EMAIL_HOST,
                                    port=self.email_config.EMAIL_PORT,
                                    use_tls=False,
                                    tls_context=context) as smtp:
                await smtp.ehlo()
                if smtp.server_auth_methods:
                    logger.debug("Server supports AUTH, assuming connection is already secure")
                else:
                    logger.debug("Starting TLS")
                    await smtp.starttls()
                    await smtp.ehlo()
                await smtp.login(self.email_config.EMAIL_ADDRESS, email_password)
                await smtp.send_message(msg)
            logger.debug("Email sent successfully")
        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            raise
        except ssl.SSLError as e:
            logger.error(f"SSL Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise

    async def _handle_retry(self, attempt: int) -> None:
        """
        Handle retry logic for failed email sends.

        Args:
            attempt (int): The current attempt number.
        """
        retry_delay = min(
            self.email_config.INITIAL_RETRY_DELAY * (2**attempt),
            self.email_config.MAX_RETRY_DELAY,
        )
        await asyncio.sleep(retry_delay)

    async def _send_via_secondary_server(self, msg: MIMEMultipart) -> None:
        """
        Attempt to send an email message via the secondary email server.

        Parameters:
        - msg (MIMEMultipart): The MIME multipart message to be sent.

        Raises:
        - ValueError: If the email password is not set in the keyring.
        - aiosmtplib.SMTPException: If there is an SMTP error on the secondary server.
        - ssl.SSLError: If there is an SSL error on the secondary server.
        - Exception: If there is an unexpected error sending the email via the secondary server.
        """
        logger.debug("Attempting to send via secondary server...")
        context = ssl.create_default_context()
        
        email_password = keyring.get_password(APP_NAME, "EMAIL_PASSWORD")
        if not email_password:
            logger.error("Email password is not set in keyring")
            raise ValueError("Email password is not set in keyring")

        try:
            async with aiosmtplib.SMTP(hostname=self.secondary_email_host,
                                    port=self.secondary_email_port,
                                    use_tls=False,
                                    tls_context=context) as smtp:
                await smtp.ehlo()
                if smtp.server_auth_methods:
                    logger.debug("Secondary server supports AUTH, assuming connection is already secure")
                else:
                    logger.debug("Starting TLS on secondary server")
                    await smtp.starttls()
                    await smtp.ehlo()
                await smtp.login(self.email_config.EMAIL_ADDRESS, email_password)
                await smtp.send_message(msg)
            logger.info("Sent email notification via secondary server.")
        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP Error on secondary server: {e}")
            raise
        except ssl.SSLError as e:
            logger.error(f"SSL Error on secondary server: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email via secondary server: {e}")
            raise

    async def close(self):
        """
        Close the Email Notification Handler.
        """
        logger.info("Closing Email Notification Handler...")
        try:
            if self.smtp_client and self.smtp_client.is_connected:
                await self.smtp_client.quit()
                logger.info("SMTP connection closed")
            else:
                logger.info("No active SMTP connection to close")
        except Exception as e:
            logger.error(f"Error during Email Notification Handler shutdown: {e}")
        finally:
            self.smtp_client = None
            logger.info("Email Notification Handler closed")


# Example usage
if __name__ == "__main__":
    async def test_email_notification():
        config = get_config()
        email_handler = EmailNotificationHandler(config)

        subject = "Test Notification"
        body = "This is a test notification from the Crypto Price Tracker."

        try:
            await email_handler.send_notification(subject, body)
            print("Test notification sent successfully.")
        except Exception as e:
            print(f"Failed to send test notification: {e}")
        finally:
            await email_handler.close()

    asyncio.run(test_email_notification())
