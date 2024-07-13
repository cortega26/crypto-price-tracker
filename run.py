import keyring
import os
import signal
import subprocess
import sys


src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
sys.path.append(src_path)

from src.gui import PriceTrackerGUI
from src.config import get_config, Config

APP_NAME = "CryptoPriceTracker"
SECURE_KEYS = ["API_KEY", "API_SECRET", "EMAIL_PASSWORD"]


def save_secure_config(config: Config):
    for key in SECURE_KEYS:
        value = getattr(config, key)
        if value:
            keyring.set_password(APP_NAME, key, value)
            setattr(config, key, None)


def load_secure_config(config: Config):
    for key in SECURE_KEYS:
        value = keyring.get_password(APP_NAME, key)
        if value:
            setattr(config, key, value)


def run_main_script(main_script):
    process = subprocess.Popen([sys.executable, main_script])

    def signal_handler(sig, frame):
        if sys.platform.startswith("win"):
            process.send_signal(signal.CTRL_C_EVENT)
        else:
            process.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


def main():
    # Run the GUI
    gui = PriceTrackerGUI()
    config_updated = gui.run_and_return()

    # Get the configuration
    config = get_config()

    if config_updated:
        print("Configuration updated. Starting the Crypto Price Tracker...")
        # Save sensitive information securely
        save_secure_config(config)
        # Save the non-sensitive parts of the configuration
        config.save_to_env_file()
    elif config.is_valid():
        print("Using existing configuration. Starting the Crypto Price Tracker...")
    else:
        print("Invalid configuration. Please update the configuration and try again.")
        return

    # Load secure configuration before running the main script
    load_secure_config(config)

    # Run main.py as a separate process
    main_script = os.path.join(src_path, "main.py")
    run_main_script(main_script)


if __name__ == "__main__":
    main()
