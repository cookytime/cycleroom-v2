import json
import requests
import time
import logging
import os
from argparse import ArgumentParser
from dotenv import load_dotenv

# Set PYTHONPATH programmatically
import sys

sys.path.append("/home/glen/cycleroom-v2/src")

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), "../config/.env")
load_dotenv(dotenv_path=dotenv_path)

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from backend.keiser_m3_ble_parser import (
        KeiserM3BLEBroadcast,
    )  # ✅ Import the new parser

    logger.info("Successfully imported KeiserM3BLEBroadcast.")
except ImportError as e:
    logger.error(f"Error importing KeiserM3BLEBroadcast: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error importing KeiserM3BLEBroadcast: {e}")
    sys.exit(1)

# Hard code the JSON file path
json_file = "/home/glen/cycleroom-v2/src/cycleroom/utils/filtered_output.json"

# Load JSON data from file
try:
    with open(json_file, "r") as file:
        data = json.load(file)
except FileNotFoundError as e:
    logger.error(f"File not found: {json_file}")
    sys.exit(1)
except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON from file {json_file}: {e}")
    sys.exit(1)

# Extract Bluetooth data
bluetooth_records = [entry for entry in data if "seconds_elapsed" in entry]

# Sort records by time (to ensure correct scheduling)
bluetooth_records.sort(key=lambda x: float(x["seconds_elapsed"]))

server_url = "http://127.0.0.1:8000/sessions"

# Get start time to sync delays
start_time = time.time()

# Process records one by one
for index, record in enumerate(bluetooth_records):
    manufacturer_data_hex = record.get("manufacturerData", "").strip()
    bluetooth_mac = record.get("id", "UNKNOWN_DEVICE")

    # Skip if `manufacturerData` is missing or empty
    if not manufacturer_data_hex:
        logger.warning(f"⚠️ Skipping device {bluetooth_mac} - No manufacturer data")
        continue

    # Skip invalid hex format
    if not all(c in "0123456789abcdefABCDEF" for c in manufacturer_data_hex):
        logger.error(
            f"❌ Skipping device {bluetooth_mac} - Invalid manufacturer data format: {manufacturer_data_hex}"
        )
        continue

    try:
        # Convert hex string to bytes
        manufacturer_data_bytes = bytes.fromhex(manufacturer_data_hex)

        # Parse the manufacturer data
        parsed_data = KeiserM3BLEBroadcast(manufacturer_data_bytes).to_dict()

        if parsed_data:
            # Extract the correct `equipment_id` from parsed data
            equipment_id = str(parsed_data.get("ordinal_id", bluetooth_mac))
            parsed_data["equipment_id"] = equipment_id
            parsed_data["bluetooth_mac"] = bluetooth_mac

            # Calculate Delay Based on `seconds_elapsed`
            elapsed_time = float(record["seconds_elapsed"])
            current_time = time.time()
            delay = max(0, start_time + elapsed_time - current_time)

            logger.info(
                f"⏳ Waiting {delay:.2f} sec before sending data for Equipment {equipment_id}..."
            )
            time.sleep(delay)  # Wait to match `seconds_elapsed`

            # Send parsed data to the server
            response = requests.post(server_url, json=parsed_data)

            if response.status_code == 200:
                logger.info(f"✅ Successfully sent data for Equipment {equipment_id}")
            else:
                logger.error(
                    f"❌ Failed to send data for {equipment_id}: {response.text}"
                )

    except Exception as e:
        logger.error(
            f"🔥 BLE Parsing Error for device {bluetooth_mac} - Data: {manufacturer_data_hex}"
        )
        logger.error(f"   Exception: {e}")
