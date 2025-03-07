import unittest
from src.cycleroom.backend.keiser_m3_ble_parser import KeiserM3BLEBroadcast
import json


class TestKeiserM3BLEBroadcast(unittest.TestCase):
    def test_initialization_and_parsing(self):
        # Load mock data from one of the JSON files
        with open("/mnt/data/2025-02-09_17-11-56.json") as f:
            mock_data = json.load(f)

        # Test with valid data (using manufacturerData from the mock data)
        data = mock_data[1][
            "manufacturerData"
        ]  # Sample manufacturerData from the mock data
        broadcast = KeiserM3BLEBroadcast(data)

        self.assertIsInstance(broadcast, KeiserM3BLEBroadcast)
        self.assertEqual(broadcast.manufacture_data, data)

        # Test with invalid data (shorter than expected)
        data_invalid = b""
        broadcast_invalid = KeiserM3BLEBroadcast(data_invalid)
        self.assertIsNone(
            broadcast_invalid.manufacture_data
        )  # Assuming the class handles it gracefully
