import asyncio
import logging
from bleak import BleakScanner
import httpx
import os

# FastAPI Endpoint to Send Parsed Data
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi-app:8000/api/bikes")

# Logger Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Target Device Prefix
TARGET_PREFIX = os.getenv("TARGET_PREFIX", "M3")

# Optimization 1: Use a set to store unique device addresses
found_bikes = set()


# Optimization 2: Use a coroutine for the detection callback
async def detection_callback(device, advertisement_data):
    if device.name and device.name.startswith(TARGET_PREFIX):
        try:
            manufacturer_data = advertisement_data.manufacturer_data.get(0x0645)
            if manufacturer_data:
                parsed_data = {
                    "device_name": device.name,
                    "device_address": device.address,
                }
                if device.address not in found_bikes:
                    found_bikes.add(device.address)
                    logger.info(
                        f"✅ Found Keiser Bike {device.name} ({device.address}) → {parsed_data}"
                    )
                    await send_data_to_fastapi(parsed_data)
        except KeyError as e:
            logger.warning(f"⚠️ Error parsing BLE data from {device.name}: {e}")


# Optimization 3: Use a coroutine for the scanning loop
async def scan_keiser_bikes(scan_duration=10):
    scanner = BleakScanner(detection_callback)
    logger.info("🔍 Starting BLE scan...")
    await scanner.start()
    await asyncio.sleep(scan_duration)
    await scanner.stop()
    logger.info(f"🔍 Scan complete. Found {len(found_bikes)} bikes.")


# Optimization 4: Use a coroutine for sending data to FastAPI
async def send_data_to_fastapi(data):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(FASTAPI_URL, json=data)
            if response.status_code == 200:
                logger.info("✅ Successfully sent BLE data to FastAPI.")
            else:
                logger.error(
                    f"❌ Failed to send BLE data. Status Code: {response.status_code}"
                )
        except httpx.RequestError as e:
            logger.error(f"❌ Error sending data to FastAPI: {e}")


# Optimization 5: Use a coroutine for the main loop
async def main():
    while True:
        await scan_keiser_bikes()
        await asyncio.sleep(5)  # Scan every 5 seconds


if __name__ == "__main__":
    asyncio.run(main())
