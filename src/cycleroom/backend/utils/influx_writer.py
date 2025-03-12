from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os

# Set these to match your InfluxDB instance
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "my-org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "ble_data")

client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)

write_api = client.write_api(write_options=SYNCHRONOUS)

def write_broadcast_data(device_name: str, parsed: object):
    point = (
        Point("m3i_broadcast")
        .tag("bike_id", parsed.id)
        .tag("device_address", parsed.uuid)
        .field("cadence_rpm", parsed.cadence)
        .field("heart_rate_bpm", parsed.heart_rate)
        .field("power_watts", parsed.power)
        .field("energy_kcal", parsed.energy)
        .field("trip_miles", parsed.trip)
        .field("time_seconds", parsed.time)
        .field("gear", parsed.gear)
        .field("build_major", parsed.build_major)
        .field("build_minor", parsed.build_minor)
        .field("interval", parsed.interval_value)
        .field("is_real_time", int(parsed.is_real_time))
        .field("speed", parsed.speed)
    )

    try:
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        return True, None
    except Exception as e:
        return False, str(e)
