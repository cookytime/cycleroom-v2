
import unittest
from unittest.mock import patch, MagicMock
import json
from src.cycleroom.backend.ble_listener import scan_keiser_bikes
from src.cycleroom.backend.keiser_m3_ble_parser import KeiserM3BLEBroadcast

class TestScanKeiserBikes(unittest.TestCase):
    @patch('cycleroom.backend.ble_listener.BleakScanner')
    @patch('cycleroom.backend.ble_listener.asyncio.sleep', return_value=None)  # Mock asyncio.sleep
    async def test_scan_keiser_bikes(self, mock_sleep, MockBleakScanner):
        # Load mock Bluetooth data from one of the JSON files
        with open('/mnt/data/2025-02-09_17-11-56.json') as f:
            mock_data = json.load(f)

        # Simulate the scanning of Bluetooth devices by mocking BleakScanner
        mock_bike = MagicMock()
        mock_bike.rssi = mock_data[1]['rssi']  # Use the rssi value from the mock data
        mock_bike.manufacturer_data = mock_data[1]['manufacturerData']  # Use the manufacturerData from mock data
        
        MockBleakScanner.discover.return_value = [mock_bike]

        # Call the scan function
        await scan_keiser_bikes()

        # Check if BleakScanner.discover was called
        MockBleakScanner.discover.assert_called_once_with(timeout=10)

        # Additional checks could be done here to confirm that the mock data is processed correctly
        broadcast = KeiserM3BLEBroadcast(mock_bike.manufacturer_data)
        self.assertEqual(broadcast.manufacture_data, mock_bike.manufacturer_data)
