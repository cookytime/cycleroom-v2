import json
import requests
import sys
import os
import time

def read_json_file(file_path):
    """Read and parse a JSON file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' contains invalid JSON.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)

def extract_bluetooth_data(data):
    """Extract relevant bluetooth device data from the JSON with timing information."""
    bluetooth_devices = []
    
    for item in data:
        # Check if this is a bluetooth sensor entry
        if "sensor" in item and item["sensor"].startswith("bluetooth-"):
            # Extract the required fields
            device_data = {
                "device_name": item.get("sensor", "").replace("bluetooth-", ""),
                "device_address": item.get("id", ""),
                "manufacturer_data": {"raw": item.get("manufacturerData", "")},
                "seconds_elapsed": float(item.get("seconds_elapsed", "0"))
            }
            bluetooth_devices.append(device_data)
    
    # Sort devices by seconds_elapsed to maintain chronological order
    bluetooth_devices.sort(key=lambda x: x["seconds_elapsed"])
    
    return bluetooth_devices

def send_data_to_api(devices, api_endpoint):
    """Send the device data to the specified API endpoint with timing based on seconds_elapsed."""
    try:
        # Get the first timestamp as a reference
        if not devices:
            return
            
        first_timestamp = devices[0]["seconds_elapsed"]
        start_time = time.time()
        
        for i, device in enumerate(devices):
            # Calculate how much time should have passed since start based on the device's timestamp
            elapsed = device["seconds_elapsed"] - first_timestamp
            
            # Calculate how much time has actually passed
            current_elapsed = time.time() - start_time
            
            # If we need to wait to match the original timing, do so
            wait_time = elapsed - current_elapsed
            if wait_time > 0:
                print(f"Waiting {wait_time:.2f} seconds to match original timing...")
                time.sleep(wait_time)
            
            # Create a copy of the device data without the seconds_elapsed field
            api_data = {
                "device_name": device["device_name"],
                "device_address": device["device_address"],
                "manufacturer_data": device["manufacturer_data"]
            }
            
            # Send the data
            print(f"Sending data for device: {device['device_address']} (original timing: {device['seconds_elapsed']:.2f}s)")
            response = requests.post(api_endpoint, json=api_data)
            
            if response.status_code == 200:
                print(f"✓ Success!")
            else:
                print(f"✗ Failed! Status code: {response.status_code}")
                print(f"  Response: {response.text}")
    
    except requests.RequestException as e:
        print(f"API request error: {str(e)}")
        sys.exit(1)

def main():
    # Default API endpoint
    default_api_endpoint = "http://cycleroom:8000/parse_raw_data"
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python script.py <json_file_path> [api_endpoint]")
        print(f"If api_endpoint is not provided, default is {default_api_endpoint}")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    # Use provided API endpoint or fall back to default
    api_endpoint = sys.argv[2] if len(sys.argv) > 2 else default_api_endpoint
    
    # Read and parse the JSON file
    data = read_json_file(json_file_path)
    
    # Extract the bluetooth device data
    bluetooth_devices = extract_bluetooth_data(data)
    
    if not bluetooth_devices:
        print("No bluetooth device data found in the JSON file.")
        sys.exit(0)
    
    # Send the data to the API
    print(f"Found {len(bluetooth_devices)} bluetooth devices in the file.")
    print(f"Sending data to {api_endpoint} with original timing...")
    send_data_to_api(bluetooth_devices, api_endpoint)
    print("All data sent successfully!")

if __name__ == "__main__":
    main()
