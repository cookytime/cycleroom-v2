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


@router.get("/bikes", tags=["Bike Data"], response_model=Dict[str, Any])
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
