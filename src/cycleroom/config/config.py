import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

# Debug: Print loaded environment variables
print(f"Loaded .env from: {dotenv_path}")
print(f"INFLUXDB_URL: {os.getenv('INFLUXDB_URL')}")
print(f"INFLUXDB_TOKEN: {os.getenv('INFLUXDB_TOKEN')}")
print(f"INFLUXDB_ORG: {os.getenv('INFLUXDB_ORG')}")
print(f"INFLUXDB_BUCKET: {os.getenv('INFLUXDB_BUCKET')}")

class Config:
    # InfluxDB Configuration
    INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "default_token")
    INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "default_org")
    INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "default_bucket")
    QUERY_INTERVAL = int(os.getenv("QUERY_INTERVAL", 2))

    # Pygame and Visualization Configuration
    SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", 1200))
    SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", 600))
    TRACK_WIDTH = int(os.getenv("TRACK_WIDTH", 800))
    TRACK_LENGTH_MILES = float(os.getenv("TRACK_LENGTH_MILES", 3.0))

    # Asset Paths
    WAYPOINTS_FILE = os.getenv("WAYPOINTS_FILE", "assets/waypoints.json")
    BIKE_ICON_PATH = os.getenv("BIKE_ICON_PATH", "assets/bike_icon.png")
    TRACK_IMAGE_PATH = os.getenv("TRACK_IMAGE_PATH", "assets/track.jpg")

# Debug: Print Config class variables
print(f"Config.INFLUXDB_URL: {Config.INFLUXDB_URL}")
print(f"Config.INFLUXDB_TOKEN: {Config.INFLUXDB_TOKEN}")
print(f"Config.INFLUXDB_ORG: {Config.INFLUXDB_ORG}")
print(f"Config.INFLUXDB_BUCKET: {Config.INFLUXDB_BUCKET}")
