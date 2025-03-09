"""
Main entry point for Cycleroom.
Starts the FastAPI server from server.py.
"""

import uvicorn
import multiprocessing
import os
import sys
import logging
from config.config import Config
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Print InfluxDB variables
influx_vars = ["INFLUXDB_URL", "INFLUXDB_TOKEN", "INFLUXDB_ORG", "INFLUXDB_BUCKET"]
for var in influx_vars:
    logger.info(f"{var}: {getattr(Config, var, 'Not Set')}")


def set_env_variables():
    """Set environment variables from Config class."""
    os.environ["INFLUXDB_URL"] = Config.INFLUXDB_URL
    os.environ["INFLUXDB_TOKEN"] = Config.INFLUXDB_TOKEN
    os.environ["INFLUXDB_ORG"] = Config.INFLUXDB_ORG
    os.environ["INFLUXDB_BUCKET"] = Config.INFLUXDB_BUCKET
    os.environ["QUERY_INTERVAL"] = str(Config.QUERY_INTERVAL)
    os.environ["SCREEN_WIDTH"] = str(Config.SCREEN_WIDTH)
    os.environ["SCREEN_HEIGHT"] = str(Config.SCREEN_HEIGHT)
    os.environ["TRACK_WIDTH"] = str(Config.TRACK_WIDTH)
    os.environ["TRACK_LENGTH_MILES"] = str(Config.TRACK_LENGTH_MILES)
    os.environ["WAYPOINTS_FILE"] = Config.WAYPOINTS_FILE
    os.environ["BIKE_ICON_PATH"] = Config.BIKE_ICON_PATH
    os.environ["TRACK_IMAGE_PATH"] = Config.TRACK_IMAGE_PATH


def start_server():
    """Starts the FastAPI server."""
    logger.info("🚀 Starting Cycleroom FastAPI server...")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=False)


def start_race():
    """Starts the Race Dashboard."""
    logger.info("🚀🚦 Starting the Race Dashboard")
    uvicorn.run("race.race:app", host="0.0.0.0", port=8001, reload=False)


def start_blescanner():
    """Starts the BLE Scanner."""
    logger.info("🚀🚦 Starting the BLE Scanner")
    uvicorn.run("backend.ble_listener:app", host="0.0.0.0", port=8002, reload=False)


if __name__ == "__main__":
    set_env_variables()
    sys.path.append("/home/glen/cycleroom-v2/src")  # Add this line to set PYTHONPATH

    multiprocessing.set_start_method("spawn")

    server_process = multiprocessing.Process(target=start_server)
    race_process = multiprocessing.Process(target=start_race)
    blescanner_process = multiprocessing.Process(target=start_blescanner)

    server_process.start()
    race_process.start()
    blescanner_process.start()

    try:
        server_process.join()
        race_process.join()
        blescanner_process.join()
    except KeyboardInterrupt:
        logger.info("Shutting down processes...")
        server_process.terminate()
        race_process.terminate()
        blescanner_process.terminate()
