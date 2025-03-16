from bleak import BleakScanner
import asyncio

async def main():
    scanner = BleakScanner()
    await scanner.start()
    print("Scanning for BLE devices...")
    
    await asyncio.sleep(10)  # Scan for 10 seconds
    await scanner.stop()
    print("Scanning stopped.")

if __name__ == "__main__":
    asyncio.run(main())