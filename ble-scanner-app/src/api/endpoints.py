from fastapi import APIRouter, HTTPException
from src.ble.scanner import BLEScanner

router = APIRouter()
scanner = BLEScanner()

@router.post("/start-scan")
async def start_scan(duration: int = 10):
    try:
        await scanner.start_scan(duration)
        return {"message": "Scan started", "duration": duration}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-scan")
async def stop_scan():
    try:
        await scanner.stop_scan()
        return {"message": "Scan stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scanned-devices")
async def get_scanned_devices():
    devices = scanner.get_scanned_devices()
    return {"devices": devices}