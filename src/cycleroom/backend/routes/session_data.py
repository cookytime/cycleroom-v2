from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from influxdb_client import Point, InfluxDBClient
from datetime import datetime, timezone
from backend.routes.bike_websocket import broadcast_ws
import os
import logging

router = APIRouter()
# Logger Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize InfluxDB client and write API using environment variables
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api()


@router.post("/sessions")
async def create_session(data: Dict[str, Any]):
    required_keys = [
        "equipment_id",
        "timestamp",
        "power",
        "gear",
        "distance",
        "cadence",
        "heart_rate",
        "caloric_burn",
        "duration_minutes",
        "duration_seconds",
    ]
    if not all(key in data for key in required_keys):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        # Convert timestamp from JSON input
        timestamp = datetime.fromisoformat(data["timestamp"]).replace(
            tzinfo=timezone.utc
        )

        # Create InfluxDB data point
        point = (
            Point("keiser_m3")
            .tag("equipment_id", str(data["equipment_id"]))
            .field("power", int(data["power"]))
            .field("cadence", int(data["cadence"]))
            .field("heart_rate", int(data["heart_rate"]))
            .field("gear", int(data["gear"]))
            .field("caloric_burn", int(data["caloric_burn"]))
            .field("duration_minutes", int(data["duration_minutes"]))
            .field("duration_seconds", int(data["duration_seconds"]))
            .field("distance", int(data["distance"]))
            .time(timestamp)
        )

        # Write to InfluxDB
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        logger.info(f"✅ Data written to InfluxDB for equipment_id: {data['equipment_id']}")
    except Exception as e:
        logger.error(f"🔥 Error Writing to InfluxDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Write data to websocket
    logger.info(f"Broadcasting data to WebSocket clients: {data}")
    await broadcast_ws(data)
    return {"message": "Session saved and sent successfully", "data": data}





