from bleak import BleakScanner
import asyncio
import logging

logger = logging.getLogger(__name__)

class BLEScanner:
    def __init__(self):
        self.scanner = BleakScanner()
        self.found_devices = set()

    async def detection_callback(self, device, advertisement_data):
        logger.info(f"Device detected: {device.name} ({device.address})")
        if device.address not in self.found_devices:
            self.found_devices.add(device.address)
            logger.info(f"Found new device: {device.name} ({device.address})")

    async def start_scanning(self, scan_duration=10):
        logger.info("Starting BLE scan...")
        await self.scanner.start(self.detection_callback)
        await asyncio.sleep(scan_duration)
        await self.scanner.stop()
        logger.info("BLE scan stopped.")

    def get_found_devices(self):
        return list(self.found_devices)

    def clear_found_devices(self):
        self.found_devices.clear()
        logger.info("Cleared found devices.")