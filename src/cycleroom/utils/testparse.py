import csv
import binascii
import requests
import json
import logging
import argparse

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Broadcast:
    def __init__(self):
        self.IsValid = False
        self.UUID = ""
        self.RSSI = 0
        self.BuildMajor = 0
        self.BuildMinor = 0
        self.Interval = 0
        self.ID = 0
        self.Cadence = 0
        self.HeartRate = 0
        self.Power = 0
        self.Energy = 0
        self.Time = 0
        self.Trip = 0
        self.Gear = None


def two_byte_concat(lower, higher):
    return (higher << 8) | lower


def build_value_convert(value):
    try:
        return int(format(value, "X"))  # Convert byte to hex, then to int
    except ValueError:
        return 0


def parse(address, advertising_data, rssi):
    broadcast = Broadcast()
    broadcast.UUID = address
    broadcast.RSSI = rssi
    broadcast.IsValid = False  # Start as invalid

    # Validate length
    if len(advertising_data) < 4 or len(advertising_data) > 19:
        return broadcast

    index = 0

    # Skip prefix bits if they exist
    if advertising_data[index] == 2 and advertising_data[index + 1] == 1:
        index += 2

    # Assign build values
    broadcast.BuildMajor = build_value_convert(advertising_data[index])
    index += 1
    broadcast.BuildMinor = build_value_convert(advertising_data[index])
    index += 1

    if broadcast.BuildMajor == 6 and len(advertising_data) > (index + 13):
        broadcast.Interval = advertising_data[index]
        broadcast.ID = advertising_data[index + 1]
        broadcast.Cadence = (
            two_byte_concat(advertising_data[index + 2], advertising_data[index + 3])
            / 10
        )
        broadcast.HeartRate = (
            two_byte_concat(advertising_data[index + 4], advertising_data[index + 5])
            / 10
        )
        broadcast.Power = two_byte_concat(
            advertising_data[index + 6], advertising_data[index + 7]
        )
        broadcast.Energy = two_byte_concat(
            advertising_data[index + 8], advertising_data[index + 9]
        )
        broadcast.Time = (
            advertising_data[index + 10] * 60 + advertising_data[index + 11]
        )
        broadcast.Trip = two_byte_concat(
            advertising_data[index + 12], advertising_data[index + 13]
        )

        # Convert miles to km if necessary
        if (broadcast.Trip & 32768) != 0:
            broadcast.Trip = int(broadcast.Trip * 1.60934)

        # Additional parameters (if BuildMinor >= 21)
        if broadcast.BuildMinor >= 21 and len(advertising_data) > (index + 14):
            broadcast.Gear = advertising_data[index + 14]

        broadcast.IsValid = True

    return broadcast


def hex_string_to_byte_array(hex_string):
    """Convert a hex string to a byte array"""
    try:
        return binascii.unhexlify(hex_string)
    except binascii.Error:
        logger.error(f"Non-hexadecimal digit found in string: {hex_string}")
        return None


def send_parsed_data_to_api(parsed_data, server_url):
    """Send parsed data to the API"""
    data = {
        "UUID": parsed_data.UUID,
        "RSSI": parsed_data.RSSI,
        "BuildMajor": parsed_data.BuildMajor,
        "BuildMinor": parsed_data.BuildMinor,
        "Interval": parsed_data.Interval,
        "ID": parsed_data.ID,
        "Cadence": parsed_data.Cadence,
        "HeartRate": parsed_data.HeartRate,
        "Power": parsed_data.Power,
        "Energy": parsed_data.Energy,
        "Time": parsed_data.Time,
        "Trip": parsed_data.Trip,
        "Gear": parsed_data.Gear,
        "IsValid": parsed_data.IsValid,
    }

    response = requests.post(server_url, json=data)
    if response.status_code == 200:
        logger.info(f"✅ Successfully sent data for UUID {parsed_data.UUID}")
    else:
        logger.error(f"❌ Failed to send data for UUID {parsed_data.UUID}: {response.text}")


def process_csv_file(csv_file, server_url):
    """Read and process the CSV file, then send data to the API"""
    with open(csv_file, newline="") as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header row

        for row in reader:
            address = row[3].strip()
            manufacturer_data = row[4].strip()
            rssi = int(row[2].strip())

            # Validate manufacturer data
            if not all(c in "0123456789abcdefABCDEF" for c in manufacturer_data):
                logger.error(f"Invalid manufacturer data: {manufacturer_data}")
                continue

            advertising_data = hex_string_to_byte_array(manufacturer_data)
            if advertising_data is None:
                continue

            parsed_data = parse(address, advertising_data, rssi)

            print(
                f"Parsed Data -> UUID: {parsed_data.UUID}, Power: {parsed_data.Power}, Cadence: {parsed_data.Cadence}, Valid: {parsed_data.IsValid}"
            )

            # Send parsed data to the API
            send_parsed_data_to_api(parsed_data, server_url)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process and send Bluetooth data from CSV file.")
    parser.add_argument("--csv-file", type=str, required=True, help="Path to the CSV file")
    parser.add_argument("--server-url", type=str, default="http://127.0.0.1:8000/sessions", help="Server URL to send data to")
    args = parser.parse_args()

    # Process the CSV file and send data to the API
    process_csv_file(args.csv_file, args.server_url)
