
import unittest
from unittest.mock import patch, MagicMock
import json
from src.cycleroom.backend.ble_scanner import send_parsed_data  # Hypothetical function for sending data

class TestSendParsedData(unittest.TestCase):
    @patch('cycleroom.backend.ble_scanner.httpx.post')
    def test_send_parsed_data(self, mock_post):
        # Load mock Bluetooth data from one of the JSON files
        with open('/mnt/data/2025-02-09_17-11-56.json') as f:
            mock_data = json.load(f)

        # Sample data to send (using mock Bluetooth data)
        data_to_send = {
            'rssi': mock_data[1]['rssi'],
            'manufacturerData': mock_data[1]['manufacturerData']
        }

        # Setup mock response from httpx.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the function
        result = send_parsed_data(data_to_send)

        # Ensure httpx.post was called
        mock_post.assert_called_once_with(
            'http://fastapi-app:8000/api/bikes', json=data_to_send
        )
        
        # Check the result (successful HTTP request)
        self.assertTrue(result)
