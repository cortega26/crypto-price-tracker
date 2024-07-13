import tkinter as tk
from tkinter import messagebox, ttk
import configparser
import keyring
import logging
from typing import Dict, Callable
import re

from config import Config, get_config

CONFIG_FILE = ".env"
APP_NAME = "CryptoPriceTracker"
SECURE_KEYS = ["API_KEY", "API_SECRET", "EMAIL_PASSWORD"]

logging.basicConfig(
    filename="price_tracker_gui.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class PriceTrackerGUI(tk.Tk):
    """
    Main GUI class for the Crypto Price Tracker Configuration.

    This class creates the main window and manages all GUI interactions.
    """

    def __init__(self):
        super().__init__()
        self.title("Crypto Price Tracker Configuration")
        self.geometry("500x670")
        self.resizable(False, False)
        self.config = configparser.ConfigParser()
        self.api_vars: Dict[str, tk.StringVar] = self._create_string_vars(
            ["API_KEY", "API_SECRET"]
        )
        self.email_vars: Dict[str, tk.StringVar] = self._create_string_vars(
            [
                "EMAIL_HOST",
                "EMAIL_PORT",
                "EMAIL_ADDRESS",
                "EMAIL_PASSWORD",
                "EMAIL_RECIPIENTS",
            ]
        )
        self.notification_vars: Dict[str, tk.StringVar] = self._create_string_vars(
            [
                "SYMBOLS_OF_INTEREST",
                "NOTIFICATION_THRESHOLD",
                "NOTIFICATION_INTERVAL",
                "DAILY_DIGEST_TIME",
                "PERCENTAGE_CHANGE_TIMEFRAME",
            ]
        )
        self.help_texts: Dict[str, str] = self._load_help_texts()
        self.create_widgets()
        self.load_existing_config()
        self.config_saved = False
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_string_vars(self, keys: list[str]) -> Dict[str, tk.StringVar]:
        """
        Create StringVar objects for a list of keys.

        Args:
            keys (list[str]): List of keys to create StringVars for.

        Returns:
            Dict[str, tk.StringVar]: Dictionary of StringVar objects.
        """
        return {key: tk.StringVar() for key in keys}

    def _load_help_texts(self) -> Dict[str, str]:
        """
        Load help texts for each configuration field.

        Returns:
            Dict[str, str]: Dictionary of help texts.
        """
        return {
            "API_KEY": "Binance API key. Create one at https://www.binance.com/en/my/settings/api-management",
            "API_SECRET": "Binance API secret. Keep this confidential.",
            "EMAIL_HOST": "SMTP server address. For Gmail: smtp.gmail.com, Outlook: smtp-mail.outlook.com",
            "EMAIL_PORT": "SMTP port. Common ports: 587 (TLS), 465 (SSL). Check your email provider's settings.",
            "EMAIL_ADDRESS": "Your email address for sending notifications.",
            "EMAIL_PASSWORD": "Email password or app-specific password. For Gmail, use an app password.",
            "EMAIL_RECIPIENTS": "Email addresses to receive alerts. Separate multiple addresses with commas.",
            "SYMBOLS_OF_INTEREST": "Crypto symbols to track, e.g., BTCUSDT,ETHUSDT,ADAUSDT. Leave blank for all USDT futures.",
            "NOTIFICATION_THRESHOLD": "Percentage change to trigger an alert. E.g., 5.0 for 5% change. Default: 1.0",
            "NOTIFICATION_INTERVAL": "Minimum seconds between notifications to avoid spam. Default: 3600 (1 hour)",
            "DAILY_DIGEST_TIME": "Time for daily summary in 24-hour format. E.g., 20:00 for 8:00 PM",
            "PERCENTAGE_CHANGE_TIMEFRAME": "Time frame in seconds to calculate % change. Default: 3600 (1 hour)",
        }

    def create_widgets(self):
        """Create and arrange all widgets in the main window."""
        main_frame = ttk.Frame(self, padding="20 10 20 0")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_section(
            main_frame, "Binance API Configuration", self.api_vars, show_secret=True
        )
        self._create_section(
            main_frame, "Email Configuration", self.email_vars, show_password=True
        )
        self._create_section(
            main_frame, "Notification Configuration", self.notification_vars
        )

        save_button = ttk.Button(
            main_frame, text="Save Configuration", command=self.save_config
        )
        save_button.pack(pady=5, ipady=5, padx=5, ipadx=5)

        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self, textvariable=self.status_var, anchor="w")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    def _create_section(
        self,
        parent: ttk.Frame,
        title: str,
        vars_dict: Dict[str, tk.StringVar],
        show_secret: bool = False,
        show_password: bool = False,
    ):
        """
        Create a section in the GUI for a group of related configuration options.

        Args:
            parent (ttk.Frame): Parent frame to add the section to.
            title (str): Title of the section.
            vars_dict (Dict[str, tk.StringVar]): Dictionary of StringVars for the section.
            show_secret (bool, optional): Whether to show secrets as asterisks. Defaults to False.
            show_password (bool, optional): Whether to show passwords as asterisks. Defaults to False.
        """
        section_frame = ttk.LabelFrame(parent, text=title, padding="10 10 10 10")
        section_frame.pack(fill="x", pady=10)

        for label, var in vars_dict.items():
            show = None
            if (show_secret and label.endswith("SECRET")) or (
                show_password and label.endswith("PASSWORD")
            ):
                show = "*"
            self._create_labeled_entry(section_frame, label, var, show)

    def _create_labeled_entry(
        self, parent: ttk.Frame, label: str, var: tk.StringVar, show: str = None
    ):
        """
        Create a labeled entry widget with tooltip and validation.

        Args:
            parent (ttk.Frame): Parent frame to add the widget to.
            label (str): Label for the entry.
            var (tk.StringVar): StringVar to bind to the entry.
            show (str, optional): Character to show instead of actual input (for passwords). Defaults to None.
        """
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=5)

        ttk.Label(frame, text=label, width=25).pack(side="left", padx=(0, 5))
        entry = ttk.Entry(frame, textvariable=var, show=show)
        entry.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self._create_tooltip(
            entry, self.help_texts.get(label, "No help available for this field.")
        )

        validation_func = self._get_validation_func(label)
        if validation_func:
            var.trace_add(
                "write", lambda *args: self._validate_entry(label, validation_func)
            )

    def _create_tooltip(self, widget: tk.Widget, text: str):
        """
        Create a tooltip for a widget.

        Args:
            widget (tk.Widget): Widget to add tooltip to.
            text (str): Tooltip text.
        """
        ToolTip(widget, text)

    def _get_validation_func(self, label: str) -> Callable[[str], bool]:
        """
        Get the appropriate validation function for a given label.

        Args:
            label (str): Label of the field to validate.

        Returns:
            Callable[[str], bool]: Validation function.
        """
        if label == "EMAIL_PORT":
            return lambda x: x.isdigit()
        elif label in [
            "NOTIFICATION_THRESHOLD",
            "NOTIFICATION_INTERVAL",
            "PERCENTAGE_CHANGE_TIMEFRAME",
        ]:
            return lambda x: x.replace(".", "", 1).isdigit()
        elif label == "EMAIL_ADDRESS":
            return lambda x: re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", x) is not None
        elif label == "DAILY_DIGEST_TIME":
            return lambda x: re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", x) is not None
        return None

    def _validate_entry(self, label: str, validation_func: Callable[[str], bool]):
        """
        Validate an entry field.

        Args:
            label (str): Label of the field to validate.
            validation_func (Callable[[str], bool]): Function to use for validation.
        """
        value = self.api_vars.get(label, tk.StringVar()).get()
        if value and not validation_func(value):
            self._show_status(f"Invalid {label.lower().replace('_', ' ')}", "error")

    def _show_status(self, message: str, status_type: str = "info"):
        """
        Show a status message in the status bar.

        Args:
            message (str): Message to show.
            status_type (str, optional): Type of status ('info' or 'error'). Defaults to 'info'.
        """
        color = "green" if status_type == "info" else "red"
        self.status_var.set(message)
        self.status_label.config(foreground=color)
        self.after(8000, lambda: self.status_var.set(""))

    def show_help(self, label: str):
        """
        Show help text for a given label.

        Args:
            label (str): Label to show help for.
        """
        help_text = self.help_texts.get(label, "No help available for this field.")
        messagebox.showinfo(f"Help for {label}", help_text)

    def load_existing_config(self):
        """Load existing configuration from file and keyring."""
        try:
            config = get_config()
            self._load_config_values(config)
            self._show_status("Configuration loaded successfully", "info")
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            self._show_status(
                "Failed to load existing configuration. Using default values.",
                "warning",
            )
            self._set_default_values()

    def _load_config_values(self, config: Config):
        """Load config values into GUI fields."""
        for key in SECURE_KEYS:
            value = keyring.get_password(APP_NAME, key) or getattr(config, key) or ""
            if key in self.api_vars:
                self.api_vars[key].set(value)
            else:
                self.email_vars[key].set(value)

        self.email_vars["EMAIL_HOST"].set(config.EMAIL_HOST)
        self.email_vars["EMAIL_PORT"].set(str(config.EMAIL_PORT))
        self.email_vars["EMAIL_ADDRESS"].set(config.EMAIL_ADDRESS)
        self.email_vars["EMAIL_RECIPIENTS"].set(config.EMAIL_RECIPIENTS)
        self.notification_vars["SYMBOLS_OF_INTEREST"].set(config.SYMBOLS_OF_INTEREST)
        self.notification_vars["NOTIFICATION_THRESHOLD"].set(
            str(config.NOTIFICATION_THRESHOLD)
        )
        self.notification_vars["NOTIFICATION_INTERVAL"].set(
            str(config.NOTIFICATION_INTERVAL)
        )
        self.notification_vars["DAILY_DIGEST_TIME"].set(config.DAILY_DIGEST_TIME)
        self.notification_vars["PERCENTAGE_CHANGE_TIMEFRAME"].set(
            str(config.PERCENTAGE_CHANGE_TIMEFRAME)
        )

    def _set_default_values(self):
        """Set default values for all fields."""
        default_config = Config()
        self._load_config_values(default_config)

    def validate_inputs(self) -> bool:
        """
        Validate all input fields.

        Returns:
            bool: True if all inputs are valid, False otherwise.
        """
        mandatory_fields = [
            ("API Key", self.api_vars["API_KEY"]),
            ("API Secret", self.api_vars["API_SECRET"]),
            ("Email Host", self.email_vars["EMAIL_HOST"]),
            ("Email Port", self.email_vars["EMAIL_PORT"]),
            ("Email Address", self.email_vars["EMAIL_ADDRESS"]),
            ("Email Password", self.email_vars["EMAIL_PASSWORD"]),
            ("Email Recipients", self.email_vars["EMAIL_RECIPIENTS"]),
            ("Daily Digest Time", self.notification_vars["DAILY_DIGEST_TIME"]),
        ]

        for field_name, var in mandatory_fields:
            if not var.get().strip():
                self._show_status(f"{field_name} is required.", "error")
                return False

        return self._validate_types()

    def _validate_types(self) -> bool:
        """
        Validate the types of all input fields.

        Returns:
            bool: True if all types are valid, False otherwise.
        """
        validations = [
            (
                self.email_vars["EMAIL_PORT"].get(),
                int,
                "Email Port must be an integer.",
            ),
            (
                self.notification_vars["NOTIFICATION_THRESHOLD"].get(),
                float,
                "Notification Threshold must be a number.",
            ),
            (
                self.notification_vars["NOTIFICATION_INTERVAL"].get(),
                int,
                "Notification Interval must be an integer.",
            ),
            (
                self.notification_vars["PERCENTAGE_CHANGE_TIMEFRAME"].get(),
                int,
                "Percentage Change Timeframe must be an integer.",
            ),
        ]

        for value, type_func, error_msg in validations:
            try:
                type_func(value)
            except ValueError:
                self._show_status(error_msg, "error")
                return False

        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email_vars["EMAIL_ADDRESS"].get()):
            self._show_status("Invalid email address format.", "error")
            return False

        if not re.match(
            r"^([01]\d|2[0-3]):([0-5]\d)$",
            self.notification_vars["DAILY_DIGEST_TIME"].get(),
        ):
            self._show_status("Invalid digest time format. Use HH:MM", "error")
            return False

        symbols = self.notification_vars["SYMBOLS_OF_INTEREST"].get().split(",")
        if symbols[0] and not all(
            re.match(r"^[A-Z0-9]+$", symbol.strip()) for symbol in symbols
        ):
            self._show_status(
                "Invalid symbols format. Use comma-separated uppercase alphanumeric symbols",
                "error",
            )
            return False

        return True

    def save_config(self):
        """Save the configuration to file and keyring."""
        try:
            if not self.validate_inputs():
                return

            config_dict = {
                "API_KEY": self.api_vars["API_KEY"].get(),
                "API_SECRET": self.api_vars["API_SECRET"].get(),
                "EMAIL_HOST": self.email_vars["EMAIL_HOST"].get(),
                "EMAIL_PORT": int(self.email_vars["EMAIL_PORT"].get()),
                "EMAIL_ADDRESS": self.email_vars["EMAIL_ADDRESS"].get(),
                "EMAIL_PASSWORD": self.email_vars["EMAIL_PASSWORD"].get(),
                "EMAIL_RECIPIENTS": self.email_vars["EMAIL_RECIPIENTS"].get(),
                "SYMBOLS_OF_INTEREST": self.notification_vars[
                    "SYMBOLS_OF_INTEREST"
                ].get(),
                "NOTIFICATION_THRESHOLD": float(
                    self.notification_vars["NOTIFICATION_THRESHOLD"].get()
                ),
                "NOTIFICATION_INTERVAL": int(
                    self.notification_vars["NOTIFICATION_INTERVAL"].get()
                ),
                "DAILY_DIGEST_TIME": self.notification_vars["DAILY_DIGEST_TIME"].get(),
                "PERCENTAGE_CHANGE_TIMEFRAME": int(
                    self.notification_vars["PERCENTAGE_CHANGE_TIMEFRAME"].get()
                ),
            }

            for key in SECURE_KEYS:
                if config_dict[key]:
                    keyring.set_password(APP_NAME, key, config_dict[key])
                    config_dict[key] = None

            new_config = Config(**config_dict)
            new_config.save_to_env_file()

            self._show_status("Configuration saved successfully", "info")
            logging.info("Configuration saved successfully")
            self.config_saved = True
            self.after(100, self.destroy)
        except Exception as e:
            error_message = f"An error occurred while saving: {str(e)}"
            logging.error(error_message)
            self._show_status(error_message, "error")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit without saving?"):
            self.destroy()

    def _save_secure_data(self):
        """Save secure data to keyring."""
        secure_keys = [
            ("API_KEY", self.api_vars),
            ("API_SECRET", self.api_vars),
            ("EMAIL_PASSWORD", self.email_vars),
        ]
        for key, vars_dict in secure_keys:
            keyring.set_password(APP_NAME, key, vars_dict[key].get())

    def _save_config_file(self):
        """Save configuration to file."""
        self.config["EMAIL"] = {
            k: v.get() for k, v in self.email_vars.items() if k != "EMAIL_PASSWORD"
        }
        self.config["NOTIFICATION"] = {
            k: v.get() for k, v in self.notification_vars.items()
        }

        with open(CONFIG_FILE, "w") as configfile:
            self.config.write(configfile)

    def run_and_return(self):
        self.mainloop()
        return self.validate_inputs() and self.config_saved


class ToolTip:
    """
    Create a tooltip for a given widget.
    """

    def __init__(self, widget, text):
        """
        Initialize the ToolTip.

        Args:
            widget: The widget to add the tooltip to.
            text: The text of the tooltip.
        """
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Display the tooltip."""
        x = y = 0
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


if __name__ == "__main__":
    app = PriceTrackerGUI()
    app.mainloop()
