# BLE Scanner Application

## Overview
The BLE Scanner Application is a Python-based project designed to scan for Bluetooth Low Energy (BLE) devices. It provides an API to manage the scanning process and retrieve information about detected devices.

## Project Structure
```
ble-scanner-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── ble
│   │   ├── scanner.py         # Implementation of BLE scanning functionality
│   │   └── __init__.py        # Package initialization for BLE
│   ├── api
│   │   ├── endpoints.py       # API endpoints for managing scans
│   │   └── __init__.py        # Package initialization for API
│   └── utils
│       ├── logger.py          # Logging configuration and utilities
│       └── __init__.py        # Package initialization for utils
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
└── .env                        # Environment variables
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd ble-scanner-app
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables in the `.env` file as needed.

## Usage
To start the BLE scanner application, run the following command:
```
python src/main.py
```

## API Endpoints
- **Start Scan**: Initiates the BLE scanning process.
- **Stop Scan**: Stops the ongoing BLE scan.
- **Get Scanned Devices**: Retrieves a list of devices detected during the scan.

## Logging
The application uses a logging utility to log messages throughout the application. You can configure the logging level in the `src/utils/logger.py` file.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.