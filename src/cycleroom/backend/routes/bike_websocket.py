from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import logging
import asyncio
import weakref

router = APIRouter()
logger = logging.getLogger(__name__)

active_connections: Dict[str, weakref.WeakSet] = {}

async def connect(websocket: WebSocket, equipment_id: str):
    await websocket.accept()
    if equipment_id not in active_connections:
        active_connections[equipment_id] = weakref.WeakSet()
    active_connections[equipment_id].add(websocket)
    logger.info(f"WebSocket connection established for equipment_id: {equipment_id}")

async def disconnect(websocket: WebSocket, equipment_id: str):
    if equipment_id in active_connections:
        active_connections[equipment_id].remove(websocket)
        if not active_connections[equipment_id]:
            del active_connections[equipment_id]
        logger.info(f"WebSocket connection closed for equipment_id: {equipment_id}")

async def broadcast_ws(data: Dict[str, Any]):
    """
    Broadcasts data to all active WebSocket clients for a given equipment_id.

    Args:
        data (Dict[str, Any]): A dictionary containing the data to be broadcasted. 
                               Expected keys are "equipment_id", "power", "gear", 
                               "distance", "cadence", "heart_rate", "caloric_burn", 
                               and "timestamp".
    """
    equipment_id = str(data.get("equipment_id"))
    if equipment_id in active_connections:
        logger.info(f"Sending data to WebSocket clients for equipment_id: {equipment_id}")
        try:
            await asyncio.gather(
                *[
                    websocket.send_json(data)
                    for websocket in active_connections[equipment_id]
                ]
            )
            logger.info(f"Data sent to WebSocket clients for equipment_id: {equipment_id}")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error sending data to WebSocket clients for equipment_id: {equipment_id}: {e}")
            return {"status": "error", "message": str(e)}
    else:
        logger.warning(f"No active WebSocket connections for equipment_id: {equipment_id}")
        return {"status": "no active connections"}

@router.websocket("/ws/{equipment_id}")
async def websocket_endpoint(websocket: WebSocket, equipment_id: str):
    await connect(websocket, equipment_id)
    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        await disconnect(websocket, equipment_id)

