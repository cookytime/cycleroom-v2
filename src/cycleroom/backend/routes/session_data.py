from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from backend.utils.db_utils import get_latest_bike_data
from pydantic import BaseModel
from typing import Dict, Any
from influxdb_client import Point
import logging
from influxdb_client import InfluxDBClient
from datetime import datetime, timezone
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# ✅ WebSocket connections storage
active_connections = {}

# Initialize InfluxDB client and write API using environment variables
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api()

@router.post("/sessions")
async def create_session(data: dict):
    required_keys = ["equipment_id", "timestamp", "power", "gear", "distance", "cadence", "heart_rate", "caloric_burn", "duration_minutes", "duration_seconds"]
    if not all(key in data for key in required_keys):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        # ✅ Convert timestamp from JSON input
        timestamp = datetime.fromisoformat(data["timestamp"]).replace(tzinfo=timezone.utc)

        # ✅ Create InfluxDB data point
        point = (
            Point("keiser_m3")
            .tag("equipment_id", str(data["equipment_id"]))  # Ensure it's a string for InfluxDB
            .field("power", int(data["power"]))
            .field("cadence", int(data["cadence"]))
            .field("heart_rate", int(data["heart_rate"]))
            .field("gear", int(data["gear"]))
            .field("caloric_burn", int(data["caloric_burn"]))  # 🔥 Ensure this is an integer
            .field("duration_minutes", int(data["duration_minutes"]))
            .field("duration_seconds", int(data["duration_seconds"]))
            .field("distance", int(data["distance"]))
            .time(datetime.utcnow().replace(tzinfo=timezone.utc)) 
        )

        # ✅ Write to InfluxDB
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

        # ✅ Broadcast new data to WebSocket clients
        await broadcast_ws(data)

    except Exception as e:
        logger.error(f"🔥 Error Writing to InfluxDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Session saved successfully", "data": data}
# ✅ WebSocket Endpoint for Real-Time Streaming per Equipment
@router.websocket("/ws/{equipment_id}")
async def websocket_endpoint(websocket: WebSocket, equipment_id: str):
    await websocket.accept()
    if equipment_id not in active_connections:
        active_connections[equipment_id] = set()
    active_connections[equipment_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if equipment_id in active_connections and websocket in active_connections[equipment_id]:
            active_connections[equipment_id].remove(websocket)
            if not active_connections[equipment_id]:  # Cleanup empty connection lists
                del active_connections[equipment_id]

# ✅ Broadcast updates to WebSocket clients per Equipment
async def broadcast_ws(data):
    equipment_id = str(data["equipment_id"])
    message = {
        "power": data["power"],
        "gear": data["gear"],
        "distance": data["distance"],
        "cadence": data["cadence"],
        "heart_rate": data["heart_rate"],
        "caloric_burn": data["caloric_burn"],
        "timestamp": data["timestamp"]
    }
    if equipment_id in active_connections:
        for websocket in active_connections[equipment_id]:
            await websocket.send_json(message)