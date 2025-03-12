import os
import logging
from config.config import Config

def set_env_variables():
    """Set environment variables from Config class."""
    os.environ["INFLUXDB_URL"] = str(Config.INFLUXDB_URL)
    os.environ["INFLUXDB_TOKEN"] = str(Config.INFLUXDB_TOKEN)
    os.environ["INFLUXDB_ORG"] = str(Config.INFLUXDB_ORG)
    os.environ["INFLUXDB_BUCKET"] = str(Config.INFLUXDB_BUCKET)

    # Debug logging to verify environment variables
    logger.info(f"INFLUXDB_URL: {os.environ['INFLUXDB_URL']} (type: {type(os.environ['INFLUXDB_URL'])})")
    logger.info(f"INFLUXDB_TOKEN: {os.environ['INFLUXDB_TOKEN']} (type: {type(os.environ['INFLUXDB_TOKEN'])})")
    logger.info(f"INFLUXDB_ORG: {os.environ['INFLUXDB_ORG']} (type: {type(os.environ['INFLUXDB_ORG'])})")
    logger.info(f"INFLUXDB_BUCKET: {os.environ['INFLUXDB_BUCKET']} (type: {type(os.environ['INFLUXDB_BUCKET'])})")

# Logger Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment variables before importing other modules
set_env_variables()

from fastapi import FastAPI
from backend.routes.bike_data import router as bike_data_router
from backend.routes.historical_data import router as historical_data_router
from backend.routes.bike_websocket import router as bike_websocket_router
from backend.routes.session_data import router as session_router
from backend.routes.parse_raw_data import router as parse_raw_data_router
import uvicorn

# FastAPI App Initialization
app = FastAPI(
    title="CycleRoom API",
    description="API for real-time and historical bike race data",
    version="1.0.0",
)

# Register Modular Routers
app.include_router(bike_data_router)
app.include_router(historical_data_router)
app.include_router(session_router)
app.include_router(bike_websocket_router)
app.include_router(parse_raw_data_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "CycleRoom API is running!"}

if __name__ == "__main__":
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
