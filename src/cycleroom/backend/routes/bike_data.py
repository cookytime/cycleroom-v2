from fastapi import APIRouter, HTTPException, Request
from backend.utils.db_utils import get_latest_bike_data
from pydantic import BaseModel
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Response Model for Real-Time Bike Data
class BikeDataResponse(BaseModel):
    bike_id: str
    distance: float


@router.get("/api/bikes", tags=["Bike Data"], response_model=Dict[str, Any])
async def get_bike_data():
    """
    Retrieve real-time bike data from InfluxDB.

    Returns:
        A JSON object containing the latest distance data for each bike.
    """
    data = get_latest_bike_data()
    if not data:
        raise HTTPException(status_code=404, detail="No bike data found")
    return data


@router.post("/api/bikes", tags=["Bike Data"])
async def receive_bike_data(request: Request):
    """
    Receive BLE data from BLE Scanner.

    Request Body:
        A JSON object containing BLE data for each bike.
        Example:
        {
            "bike_1": {
                "distance": 1.5
            },
            "bike_2": {
                "distance": 2.3
            }
        }

    Returns:
        A status message confirming receipt of the data.
    """
    data = await request.json()
    logger.info(f"✅ Received BLE data: {data}")
    return {"status": "success"}
