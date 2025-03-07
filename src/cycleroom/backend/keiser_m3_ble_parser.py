import struct
from datetime import datetime, timezone

class KeiserM3BLEBroadcast:
    def __init__(self, manufacture_data: bytes):
        """Parses Keiser M3 BLE advertisement data into structured format."""
        if len(manufacture_data) <= 17:
            manufacture_data = manufacture_data[2:]  # Trim first 2 bytes

        self.build_major, self.build_minor, self.data_type, self.ordinal_id, \
        self.cadence, self.heart_rate, self.power, self.caloric_burn, \
        self.duration, temp_distance, self.gear = struct.unpack('<BBBBHHHHHHB', manufacture_data)

        # Convert cadence and heart rate
        self.cadence /= 10  # Convert to RPM
        self.heart_rate /= 10  # Convert to BPM

        # Determine real-time or review mode
        self.real_time = self.data_type in [0, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159]
        self.interval = 0 if self.data_type in [0, 255] else self.data_type if self.data_type < 128 else self.data_type - 128

        # Convert tripDistance to miles/km
        self.trip_distance = ((temp_distance & 32767) * 0.62137119) / 10.0 if temp_distance & 32768 else temp_distance / 10.0

        # Timestamp
        self.timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    def to_dict(self):
        """Convert parsed data to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "build_major": self.build_major,
            "build_minor": self.build_minor,
            "data_type": self.data_type,
            "ordinal_id": self.ordinal_id,
            "interval": self.interval,
            "real_time": self.real_time,
            "cadence": self.cadence,
            "heart_rate": self.heart_rate,
            "power": self.power,
            "caloric_burn": self.caloric_burn,
            "duration": self.duration,
            "trip_distance": self.trip_distance,
            "gear": self.gear,
        }