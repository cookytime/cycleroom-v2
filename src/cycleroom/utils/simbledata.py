import time
import random

def generate_m3_data(equipment_id, version_major=6, version_minor=30, data_type=0, cadence=0,
                     heart_rate=0, power=0, caloric_burn=0, duration_minutes=0,
                     duration_seconds=0, distance=0, gear=10, is_metric=False):
    """
    Generates Keiser M3 data packet (manufacturer specific data).

    Args:
        equipment_id:  The equipment ID (0-200).
        version_major: Major version number.
        version_minor: Minor version number.
        data_type:     Data type (0: Real Time Main, 1-99: Review, 128-227: Real Time, 255: Review Main).
        cadence:       Cadence in RPM * 10.
        heart_rate:    Heart rate in BPM * 10.
        power:         Power in watts.
        caloric_burn:  Accumulated caloric burn.
        duration_minutes: Duration in minutes.
        duration_seconds: Duration in seconds.
        distance:      Distance * 10.
        gear:          Gear (1-24).
        is_metric:     True for kilometers, False for miles.

    Returns:
        A bytearray representing the manufacturer specific data.
    """

    # --- Input Validation and Constraints ---
    if not 0 <= equipment_id <= 200:
        raise ValueError("Equipment ID must be between 0 and 200")
    if not 0 <= data_type <= 255:
        raise ValueError("Data type must be between 0 and 255")
    if not 0 <= cadence <= 65535:  # Max value for 2 bytes
        raise ValueError("Cadence is out of range (2-byte unsigned int)")
    if not 0 <= heart_rate <= 65535:
        raise ValueError("Heart Rate is out of range (2-byte unsigned int)")
    if not 0 <= power <= 65535:
        raise ValueError("Power is out of range (2-byte unsigned int)")
    if not 0 <= caloric_burn <= 65535:
        raise ValueError("Caloric Burn is out of range (2-byte unsigned int)")
    if not 0 <= duration_minutes <= 255:
        raise ValueError("Duration Minutes is out of range (1-byte unsigned int)")
    if not 0 <= duration_seconds <= 255:
        raise ValueError("Duration Seconds is out of range (1-byte unsigned int)")
    if not 0 <= distance <= 999: #  0 to 999.
        raise ValueError("Distance is out of range (0-999)")
    if not 1 <= gear <= 24:
        raise ValueError("Gear must be between 1 and 24")


    # --- Data Packing ---
    company_id = b'\x02\x01'  # Keiser Company ID
    version_major_byte = version_major.to_bytes(1, 'little')
    version_minor_byte = version_minor.to_bytes(1, 'little')
    data_type_byte = data_type.to_bytes(1, 'little')
    equipment_id_byte = equipment_id.to_bytes(1, 'little')
    cadence_bytes = cadence.to_bytes(2, 'little')
    heart_rate_bytes = heart_rate.to_bytes(2, 'little')
    power_bytes = power.to_bytes(2, 'little')
    caloric_burn_bytes = caloric_burn.to_bytes(2, 'little')
    duration_minutes_byte = int(duration_minutes).to_bytes(1, 'little')
    duration_seconds_byte = duration_seconds.to_bytes(1, 'little')

    # Distance:  Set the MSB for units.
    distance_bytes = distance.to_bytes(2, 'little')
    distance_int = int.from_bytes(distance_bytes, 'little')
    if is_metric:
        distance_int |= (1 << 15)  # Set the 16th bit (MSB)
    distance_bytes = distance_int.to_bytes(2, 'little')

    gear_byte = gear.to_bytes(1, 'little')

    # --- Concatenate Data ---
    data = bytearray(company_id)
    data.extend(version_major_byte)
    data.extend(version_minor_byte)
    data.extend(data_type_byte)
    data.extend(equipment_id_byte)
    data.extend(cadence_bytes)
    data.extend(heart_rate_bytes)
    data.extend(power_bytes)
    data.extend(caloric_burn_bytes)
    data.extend(duration_minutes_byte)
    data.extend(duration_seconds_byte)
    data.extend(distance_bytes)
    data.extend(gear_byte)

    return data


def generate_advertising_data(manufacturer_data, local_name="M3"):
    """
    Generates the full advertising data, including the manufacturer data.

    Args:
        manufacturer_data: The manufacturer-specific data bytearray.
        local_name: The local name of the device (default: "M3").

    Returns:
        A bytearray representing the full advertising data.
    """

    # --- Local Name ---
    local_name_bytes = local_name.encode('ascii')
    local_name_length = len(local_name_bytes)
    local_name_section = bytearray()
    local_name_section.append(local_name_length + 1)  # Length of the section (including type byte)
    local_name_section.append(0x09)  # Type: Complete Local Name
    local_name_section.extend(local_name_bytes)

    # --- Appearance (Unused by Keiser) ---
    appearance_section = b'\x03\x19\x00\x00'  # Length, Type, 00 00

    # --- Flags ---
    flags_section = b'\x02\x01\x04'  # Length, Type, Flags

    # --- Manufacturer Specific Data ---
    manufacturer_length = len(manufacturer_data)
    manufacturer_section = bytearray()
    manufacturer_section.append(manufacturer_length + 1)  # Length byte (including type byte)
    manufacturer_section.append(0xFF)  # Type: Manufacturer Specific Data
    manufacturer_section.extend(manufacturer_data)


    # --- Combine all sections ---
    advertising_data = bytearray(local_name_section)
    advertising_data.extend(appearance_section)
    advertising_data.extend(flags_section)
    advertising_data.extend(manufacturer_section)

    return advertising_data


def generate_broadcast_packet(advertising_data, advertising_address="db:78:3b:29:75:7e"):
    """
    Generates a (simplified) broadcast packet.  This function creates the
    parts of the packet that are typically exposed by BLE APIs.  It does *not*
    include the access address or CRC, as those are usually handled by the
    BLE stack.

    Args:
        advertising_data: The complete advertising data bytearray.
        advertising_address: The BLE advertising address (as a string).

    Returns:
        A dictionary containing the advertising address and advertising data.
        This structure is more representative of what a BLE API would provide.
    """

    # --- Advertising Address (convert from string to bytes) ---
    address_bytes = bytes.fromhex(advertising_address.replace(":", "")[::-1]) # Reverse for little-endian

    # --- Construct the packet dictionary ---
    packet = {
        "advertising_address": address_bytes,
        "advertising_data": advertising_data
    }
    return packet


def simulate_keiser_m3(equipment_id=56, duration=60):
    """
    Simulates Keiser M3 data transmission for a given duration.

    Args:
        equipment_id: The equipment ID to simulate.
        duration: The simulation duration in seconds.
    """

    start_time = time.time()
    elapsed_time = 0
    cadence = 0
    heart_rate = 0
    power = 0
    total_calories = 0
    total_distance = 0
    gear = 1

    while elapsed_time < duration:
        # --- Simulate changing values (simplified) ---
        # In a real simulation, you'd have more sophisticated models.
        cadence = int(random.uniform(60, 100) * 10)  # 60.0 to 100.0 RPM
        heart_rate = int(random.uniform(120, 150) * 10)  # 120.0 to 150.0 BPM
        power = random.randint(100, 200)  # 100 to 200 watts
        gear = random.randint(1,24)

        # Accumulate calories and distance (very simplified)
        total_calories += int(power * 0.2)  # Just a rough estimate
        total_distance += int(cadence * 0.05) # Another rough estimate.
        is_metric = random.choice([True, False])  # Randomly choose units


        # --- Generate the data packet ---
        manufacturer_data = generate_m3_data(
            equipment_id=equipment_id,
            cadence=cadence,
            heart_rate=heart_rate,
            power=power,
            caloric_burn=total_calories,
            duration_minutes=elapsed_time // 60,
            duration_seconds=int(elapsed_time % 60),
            distance=total_distance,
            gear=gear,
            is_metric=is_metric
        )

        advertising_data = generate_advertising_data(manufacturer_data)
        broadcast_packet = generate_broadcast_packet(advertising_data)

        # --- "Transmit" the packet (print to console) ---
        print(f"Time: {elapsed_time:.1f}s")
        print(f"  Advertising Address: {broadcast_packet['advertising_address'].hex(':')}")
        print(f"  Advertising Data: {broadcast_packet['advertising_data'].hex()}")

        # --- Parse the data for demonstration ---
        parsed_data = parse_manufacturer_data(manufacturer_data)
        print(f"  Parsed Data: {parsed_data}")
        print("-" * 30)

        # --- Wait and update elapsed time ---
        time.sleep(1)  # Simulate 1-second interval
        elapsed_time = time.time() - start_time


def parse_manufacturer_data(data):
    """Parses the Keiser M3 manufacturer specific data.

    Args:
        data: The manufacturer data bytearray.

    Returns:
        A dictionary containing the parsed data.
    """

    # --- Basic Checks ---
    if len(data) < 19:  # Minimum length for a valid packet
        raise ValueError("Data too short to be a valid Keiser M3 packet")
    if data[0:2] != b'\x02\x01':
        raise ValueError("Invalid Company ID")

    # --- Data Extraction ---
    parsed = {}
    parsed['company_id'] = data[0:2].hex()
    parsed['version_major'] = int(data[2])
    parsed['version_minor'] = int(data[3])
    parsed['data_type'] = int(data[4])
    parsed['equipment_id'] = int(data[5])
    parsed['cadence'] = int.from_bytes(data[6:8], 'little') / 10.0
    parsed['heart_rate'] = int.from_bytes(data[8:10], 'little') / 10.0
    parsed['power'] = int.from_bytes(data[10:12], 'little')
    parsed['caloric_burn'] = int.from_bytes(data[12:14], 'little')
    parsed['duration_minutes'] = int(data[14])
    parsed['duration_seconds'] = int(data[15])
    distance_raw = int.from_bytes(data[16:18], 'little')
    parsed['is_metric'] = bool(distance_raw & (1 << 15))  # Check the MSB
    parsed['distance'] = (distance_raw & 0x7FFF) / 10.0  # Mask out the MSB
    parsed['gear'] = int(data[18])

    return parsed


# --- Example Usage ---
if __name__ == "__main__":
    simulate_keiser_m3(equipment_id=56, duration=30)

    # Example of generating and parsing a single packet:
    print("\nSingle Packet Example:")
    m_data = generate_m3_data(equipment_id=10, cadence=852, power=150, duration_minutes=5, duration_seconds=30, distance=25, is_metric=True)
    a_data = generate_advertising_data(m_data)
    b_packet = generate_broadcast_packet(a_data)
    print(f"Generated Packet: {b_packet}")
    p_data = parse_manufacturer_data(m_data)
    print(f"Parsed Data: {p_data}")
