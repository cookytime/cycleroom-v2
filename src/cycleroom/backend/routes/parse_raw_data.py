from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict
from backend.utils.influx_writer import write_broadcast_data
import binascii
import logging

router = APIRouter()

# Logger Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Broadcast + Parser from previous conversion
class Broadcast:
    def __init__(self):
        self.is_valid = False
        self.uuid = None
        self.id = 0
        self.cadence = 0
        self.heart_rate = 0
        self.power = 0
        self.build_major = 0
        self.build_minor = 0
        self.interval = 0
        self.energy = 0
        self.trip = 0         # in kilometers (after conversion)
        self.time = 0         # in seconds
        self.rssi = 0
        self.gear = 0
        self.speed = 0.0      # <-- NEW field

    @property
    def is_real_time(self):
        return self.interval == 0 or (128 < self.interval < 255)

    @property
    def interval_value(self):
        if self.interval == 0 or self.interval == 255:
            return 0
        if 128 < self.interval < 255:
            return self.interval - 128
        return self.interval

class Parser:
    @staticmethod
    def parse(address: str, advertising_data: bytes, rssi: int) -> Broadcast:
        broadcast = Broadcast()
        broadcast.uuid = address
        broadcast.rssi = rssi

        logger.info(f"Parsing BLE data for address: {address}")
        logger.info(f"Advertising data: {advertising_data.hex()}")
        logger.info(f"RSSI: {rssi}")

        if len(advertising_data) < 4 or len(advertising_data) > 19:
            logger.warning("Invalid advertising data length")
            return broadcast

        index = 0
        if advertising_data[0] == 2 and advertising_data[1] == 1:
            index += 2

        broadcast.build_major = Parser.build_value_convert(advertising_data[index])
        index += 1
        broadcast.build_minor = Parser.build_value_convert(advertising_data[index])
        index += 1

        logger.info(f"Build major: {broadcast.build_major}, Build minor: {broadcast.build_minor}")

        if broadcast.build_major == 6 and len(advertising_data) > index + 13:
            broadcast.interval = advertising_data[index]
            broadcast.id = advertising_data[index + 1]
            broadcast.cadence = Parser.two_byte_concat(advertising_data[index + 2], advertising_data[index + 3]) // 10
            broadcast.heart_rate = Parser.two_byte_concat(advertising_data[index + 4], advertising_data[index + 5]) // 10
            broadcast.power = Parser.two_byte_concat(advertising_data[index + 6], advertising_data[index + 7])
            broadcast.energy = Parser.two_byte_concat(advertising_data[index + 8], advertising_data[index + 9])
            broadcast.time = advertising_data[index + 10] * 60 + advertising_data[index + 11]
            raw_distance = Parser.two_byte_concat(advertising_data[index + 12], advertising_data[index + 13])

            unit_is_metric = (raw_distance & 0x8000) != 0  # Check MSB
            distance_value = raw_distance & 0x7FFF         # Clear MSB (get lower 15 bits)
            distance = distance_value / 10.0               # Apply 1 decimal precision

            if not unit_is_metric:
                # Convert miles → kilometers
                distance *= 1.60934

            broadcast.trip = distance

            if broadcast.build_minor >= 21 and len(advertising_data) > index + 14:
                broadcast.gear = advertising_data[index + 14]

            # After parsing trip and time
            if broadcast.time > 0:
                broadcast.speed = (broadcast.trip / broadcast.time) * 3600  # km/h
            else:
                broadcast.speed = 0.0

            broadcast.is_valid = True

        logger.info(f"Parsed broadcast: {broadcast.__dict__}")
        return broadcast

    @staticmethod
    def two_byte_concat(lower: int, higher: int) -> int:
        return (higher << 8) | lower

    @staticmethod
    def build_value_convert(value: int) -> int:
        try:
            return int(f"{value:X}", 10)
        except ValueError:
            return 0


# Pydantic model for request body
class ManufacturerData(BaseModel):
    raw: str

class BLEPayload(BaseModel):
    device_name: str
    device_address: str
    manufacturer_data: ManufacturerData


@router.post("/parse_raw_data")
def receive_ble_data(payload: BLEPayload):
    try:
        raw_bytes = binascii.unhexlify(payload.manufacturer_data.raw)
    except binascii.Error:
        raise HTTPException(status_code=400, detail="Invalid hex in manufacturer_data.raw")

    parsed = Parser.parse(payload.device_address, raw_bytes, rssi=0)

    if not parsed.is_valid:
        raise HTTPException(status_code=422, detail="Could not parse BLE data")

    success, error = write_broadcast_data(payload.device_name, parsed)

    if not success:
        raise HTTPException(status_code=500, detail=f"InfluxDB write failed: {error}")

    return {"status": "success"}
