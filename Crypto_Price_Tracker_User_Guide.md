# Crypto Price Tracker: Comprehensive User Guide

## Table of Contents

- [Crypto Price Tracker: Comprehensive User Guide](#crypto-price-tracker-comprehensive-user-guide)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
  - [2. System Requirements](#2-system-requirements)
  - [3. Installation](#3-installation)
  - [4. Configuration](#4-configuration)
    - [Running the Configuration GUI](#running-the-configuration-gui)
    - [Understanding Configuration Fields](#understanding-configuration-fields)
      - [Binance API Configuration](#binance-api-configuration)
      - [Email Configuration](#email-configuration)
      - [Notification Configuration](#notification-configuration)
  - [5. Running the Application](#5-running-the-application)
    - [Using run.py](#using-runpy)
    - [Using main.py](#using-mainpy)
  - [6. Understanding Notifications](#6-understanding-notifications)
  - [7. Troubleshooting](#7-troubleshooting)
  - [8. FAQ](#8-faq)
  - [9. Security Considerations](#9-security-considerations)
  - [10. Support and Community](#10-support-and-community)
  - [11. API Key Security Best Practices](#11-api-key-security-best-practices)
  - [12. Using Logs for Troubleshooting](#12-using-logs-for-troubleshooting)

## 1. Introduction

Welcome to the Crypto Price Tracker! This application allows you to monitor cryptocurrency prices in real-time and receive notifications about significant price movements. Whether you're a seasoned trader or just curious about crypto markets, this tool will help you stay informed about the latest price changes.

## 2. System Requirements

- Python 3.9 or higher
- Internet connection
- Windows, macOS, or Linux operating system

## 3. Installation

1. Download the Crypto Price Tracker from <https://github.com/cortega26/crypto-price-tracker.git>.
2. Unzip the file to your desired location.
3. Open a terminal or command prompt.
4. Navigate to the unzipped folder:

   ```sh
   cd path/to/crypto-price-tracker
   ```

5. Create a virtual environment:

   ```sh
   python -m venv venv
   ```

6. Activate the virtual environment:
   - On Windows:

     ```sh
     venv\Scripts\activate
     ```

   - On macOS and Linux:

     ```sh
     source venv/bin/activate
     ```

7. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

## 4. Configuration

### Running the Configuration GUI

1. In the terminal, ensure you're in the crypto-price-tracker directory and your virtual environment is activated.
2. Run the following command:

   ```sh
   python run.py
   ```

3. This will open the configuration GUI.

### Understanding Configuration Fields

#### Binance API Configuration

- **API Key**: Your Binance API key.
  - How to get it: Log in to your Binance account, go to "API Management", and create a new API key.
  - Keep this key secret and never share it with anyone.

- **API Secret**: Your Binance API secret.
  - This is provided when you create your API key.
  - Keep this secret and never share it with anyone.

#### Email Configuration

- **Email Host**: The SMTP server address for your email provider.
  - For Gmail: smtp.gmail.com
  - For Outlook: smtp-mail.outlook.com
  - For other providers, check their SMTP settings or contact their support.

- **Email Port**: The port number for the SMTP server.
  - Common ports are 587 (for TLS) or 465 (for SSL).
  - Check your email provider's settings for the correct port.

- **Email Address**: Your email address that will send notifications.

- **Email Password**: The password for your email account.
  - IMPORTANT: For many providers (like Gmail), you'll need to use an "App Password" instead of your regular password.
  - How to create an App Password:
    1. Go to your email account settings.
    2. Look for "Security" or "App passwords".
    3. Create a new app password specifically for this application.
    4. Use this generated password in the configuration.

- **Email Recipients**: Email addresses that will receive notifications.
  - You can enter multiple addresses separated by commas.
  - Example: <user1@example.com>, <user2@example.com>

#### Notification Configuration

- **Symbols of Interest**: Cryptocurrency symbols you want to track.
  - Enter the symbols exactly as they appear on Binance.
  - Separate multiple symbols with commas.
  - Example: BTCUSDT,ETHUSDT,ADAUSDT
  - Leave blank to track all USDT futures.

- **Notification Threshold**: The percentage change that triggers an alert.
  - Enter a number (can include decimals).
  - Example: 5.0 for a 5% change.

- **Notification Interval**: Minimum time (in seconds) between notifications.
  - This prevents spam if prices are very volatile.
  - Example: 3600 for one hour.

- **Daily Digest Time**: Time to receive a daily summary.
  - Use 24-hour format (HH:MM).
  - Example: 20:00 for 8:00 PM.

- **Percentage Change Timeframe**: Time frame (in seconds) to calculate percentage change.
  - Example: 3600 for one hour.

## 5. Running the Application

You can run the Crypto Price Tracker in two ways:

### Using run.py

1. Open a terminal or command prompt.
2. Navigate to the crypto-price-tracker directory.
3. Activate your virtual environment (if not already activated).
4. Run the following command:

   ```sh
   python run.py
   ```

5. This will first open the configuration GUI if needed, then start the tracker.

### Using main.py

1. Open a terminal or command prompt.
2. Navigate to the crypto-price-tracker directory.
3. Activate your virtual environment (if not already activated).
4. Run the following command:

   ```sh
   python src/main.py
   ```

5. This will start the tracker using the existing configuration without opening the GUI.

## 6. Understanding Notifications

The Crypto Price Tracker sends several types of notifications:

1. **Price Movement Alerts**: Sent when a tracked cryptocurrency's price changes by more than the specified notification threshold within the percentage change timeframe.
2. **All-Time High (ATH) Alerts**: Sent when a tracked cryptocurrency reaches a new all-time high price.
3. **All-Time Low (ATL) Alerts**: Sent when a tracked cryptocurrency reaches a new all-time low price.
4. **90-Day High Alerts**: Sent when a tracked cryptocurrency reaches its highest price in the last 90 days.
5. **90-Day Low Alerts**: Sent when a tracked cryptocurrency reaches its lowest price in the last 90 days.
6. **Daily Digest**: A summary of the day's significant price movements, sent at the time specified in your configuration.

## 7. Troubleshooting

- **Configuration GUI doesn't open**:
  - Ensure you're in the correct directory.
  - Check that your virtual environment is activated.
  - Verify that all required packages are installed.

- **Email notifications not received**:
  - Check your spam folder.
  - Verify your email configuration, especially if using Gmail or other providers with strict security.
  - Ensure you're using an "App Password" if your email provider requires it.

- **No price updates**:
  - Check your internet connection.
  - Verify your Binance API key and secret.
  - Ensure the symbols you're tracking are valid and active on Binance.

- **Error messages**:
  - Read the error message carefully.
  - Check the log file (price_tracker_gui.log) for more details.
  - Verify all configuration fields are filled correctly.

## 8. FAQ

Q: How often does the tracker update prices?  
A: The tracker receives real-time updates from Binance's WebSocket API, so prices are updated almost instantly.

Q: Can I track cryptocurrencies from exchanges other than Binance?  
A: Currently, the tracker only supports Binance. Support for other exchanges may be added in future versions.

Q: Is my API key and other sensitive information safe?  
A: Yes, sensitive information like your API key and email password are stored securely using your system's keyring, not in plain text.

Q: Can I run the tracker on a server or Raspberry Pi?  
A: Yes, as long as the system meets the requirements and has Python installed, you can run the tracker on various platforms.

Q: What happens if my internet connection drops?  
A: The tracker will attempt to reconnect automatically. If it can't reconnect, it will log the error and exit.

## 9. Security Considerations

- Never share your Binance API key, API secret, or email password with anyone.
- Use a dedicated email account for notifications if possible.
- Regularly update your passwords and API keys.
- Keep your system and Python environment up to date.

## 10. Support and Community

This Crypto Price Tracker is an open-source project maintained by a single developer (me). While direct support is limited, there are several ways to get help, report issues, or contribute to the project:

1. **GitHub Issues**: If you encounter bugs or have feature requests, please open an issue on the project's GitHub repository. This allows for tracking and public discussion of the topic.

2. **Documentation**: This user guide and the project's README file are regularly updated. Always check these resources first for the most up-to-date information.

3. **Community Discussions**: Feel free to start or join discussions in the GitHub Discussions section of the repository. This is a great place to ask questions, share experiences, or suggest improvements.

4. **Contributing**: If you have ideas for improvements or bug fixes, contributions via pull requests are welcome!

5. **Stack Overflow**: For general programming questions related to the technologies used in this project, Stack Overflow can be a valuable resource. Use relevant tags like "python", "cryptocurrency", or "binance-api".

Remember, as an open-source project, the Crypto Price Tracker thrives on community involvement. Your feedback, bug reports, and contributions help improve the tool for everyone.

## 11. API Key Security Best Practices

To ensure the security of your Binance account and data:

- Use read-only API keys whenever possible.
- Regularly rotate your API keys (e.g., every 3-6 months).
- Set IP restrictions on your API key if supported by Binance.
- Never share your API keys or secrets with anyone.
- Monitor your API key usage regularly for any suspicious activity.

## 12. Using Logs for Troubleshooting

The price_tracker_gui.log file contains detailed information about the application's operation. To use it for troubleshooting:

1. Open the log file in a text editor.
2. Look for entries marked "ERROR" or "WARNING".
3. Check the timestamps to correlate log entries with observed issues.
4. If reporting an issue, include relevant log excerpts (make sure to remove any sensitive information).

Thank you for your interest in the Crypto Price Tracker!
