from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
import re


class Config(BaseSettings):
    # Binance API settings
    API_KEY: Optional[str] = None
    API_SECRET: Optional[str] = None

    # Email settings
    EMAIL_HOST: str = ""
    EMAIL_PORT: int = 587
    EMAIL_ADDRESS: str = ""
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_RECIPIENTS: str = ""

    # Notification settings
    SYMBOLS_OF_INTEREST: str = ""
    NOTIFICATION_THRESHOLD: float = 1.0
    NOTIFICATION_INTERVAL: int = 3600
    DAILY_DIGEST_TIME: str = "20:00"
    PERCENTAGE_CHANGE_TIMEFRAME: int = 3600

    # WebSocket settings
    MAX_RETRIES: int = 5
    INITIAL_RETRY_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 60.0

    # Cache settings
    HISTORICAL_DATA_CACHE_TTL: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def symbols_list(self) -> List[str]:
        return [
            symbol.strip()
            for symbol in self.SYMBOLS_OF_INTEREST.split(",")
            if symbol.strip()
        ]

    @field_validator("API_KEY", "API_SECRET", "EMAIL_PASSWORD")
    @classmethod
    def empty_str_to_none(cls, v: Optional[str]) -> Optional[str]:
        return None if v == "" else v

    @field_validator("API_KEY", "API_SECRET", "EMAIL_ADDRESS", "EMAIL_PASSWORD")
    @classmethod
    def non_empty_string(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("This field cannot be empty")
        return v

    @field_validator("EMAIL_PORT")
    @classmethod
    def valid_port(cls, v: int) -> int:
        if not 0 < v < 65536:
            raise ValueError("Invalid port number")
        return v

    @field_validator("EMAIL_ADDRESS")
    @classmethod
    def valid_email(cls, v: str) -> str:
        if v and not re.fullmatch(r"(^([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(\.[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+)*)\@([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,})$", v):
            raise ValueError("Invalid email address")
        return v

    @field_validator(
        "NOTIFICATION_THRESHOLD", "NOTIFICATION_INTERVAL", "PERCENTAGE_CHANGE_TIMEFRAME"
    )
    @classmethod
    def positive_number(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("This value must be positive")
        return v

    def save_to_env_file(self):
        with open(".env", "w") as env_file:
            for field, value in self.model_dump().items():
                if field not in ["API_KEY", "API_SECRET", "EMAIL_PASSWORD"]:
                    env_file.write(f"{field}={value}\n")

    def get_email_recipients(self) -> List[str]:
        return [
            email.strip() for email in self.EMAIL_RECIPIENTS.split(",") if email.strip()
        ]

    def is_valid(self) -> bool:
        """Check if the configuration is valid and contains all necessary information."""
        return all(
            [
                self.EMAIL_HOST,
                self.EMAIL_PORT,
                self.EMAIL_ADDRESS,
                self.EMAIL_RECIPIENTS,
            ]
        )


def get_config() -> Config:
    return Config()


if __name__ == "__main__":
    config = get_config()
    print(f"API Key: {config.API_KEY}")
    print(f"Email Host: {config.EMAIL_HOST}")
    print(f"Symbols of Interest: {config.symbols_list}")
    print(f"Email Recipients: {config.get_email_recipients()}")
