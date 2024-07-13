# Crypto Price Tracker

## Overview

Crypto Price Tracker is a comprehensive tool designed to monitor cryptocurrency prices in real-time, provide alerts for significant price movements, and deliver daily summaries of market activity. This project utilizes the Binance WebSocket API to stream live price data and offers customizable alerts and notifications.

## Features

- Real-time price tracking for multiple cryptocurrencies
- Customizable price alerts for all-time highs, all-time lows, and specific thresholds
- Email notifications for triggered alerts and daily price digests
- User-friendly GUI for easy configuration
- Robust error handling and automatic reconnection for WebSocket streams

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/cortega26/crypto-price-tracker.git
   cd crypto-price-tracker
   ```

2. Create a virtual environment and activate it:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

## Configuration

1. Run the configuration GUI:

   ```sh
   python run.py
   ```

2. Fill in the required fields:
   - Binance API Key and Secret
   - Email settings for notifications
   - Symbols of interest
   - Notification thresholds and intervals

3. Save the configuration. The settings will be stored in a `.env` file.

## Usage

After configuring the application, you can start the Crypto Price Tracker by running:

```sh
python run.py
```

This will:

1. Load the configuration
2. Initialize the price tracker and alert system
3. Connect to the Binance WebSocket stream
4. Begin monitoring prices and sending alerts as configured

## Key Components

- **config.py**: Manages application configuration using Pydantic for robust validation.
- **api_client.py**: Handles communication with the Binance API.
- **price_tracker.py**: Tracks and analyzes price movements.
- **alert_manager.py**: Manages alert conditions and triggers notifications.
- **notification.py**: Handles sending email notifications.
- **websocket_handler.py**: Manages the WebSocket connection for real-time data.
- **gui.py**: Provides a user-friendly interface for configuration.
- **main.py**: Orchestrates the entire application.

## Advanced Features

- **Graceful Shutdown**: The application handles SIGINT and SIGTERM signals for graceful shutdown, ensuring all resources are properly cleaned up.
- **Automatic Reconnection**: In case of WebSocket disconnection, the application will automatically attempt to reconnect with exponential backoff.
- **Efficient Data Storage**: Historical price data is stored efficiently to balance between memory usage and performance.

## Customization

You can customize various aspects of the tracker by modifying the configuration through the GUI or by directly editing the `.env` file. Advanced users can also modify the source code to add new features or alter existing functionality.

## Troubleshooting

If you encounter any issues:

1. Check the log files for error messages.
2. Ensure your Binance API key has the necessary permissions.
3. Verify your email settings if you're not receiving notifications.
4. For WebSocket connection issues, check your internet connection and Binance API status.

## Contributing

Contributions to the Crypto Price Tracker are welcome! Please feel free to submit pull requests, create issues or suggest new features.

## License

This project is licensed under the Apache License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and informational purposes only. Cryptocurrency trading involves significant risk. Always do your own research before making any trading decisions.
