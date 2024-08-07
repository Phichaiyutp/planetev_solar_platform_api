from datetime import time
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.fusionsolar.handle import ApiHandle
from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = APIRouter()
api_handle = ApiHandle()
scheduler = AsyncIOScheduler()

async def setup_scheduler(db: Session):
    scheduler.add_job(api_handle.DevRealKpi, 'interval', minutes=5, args=[db], id="job_DevRealKpi")
    scheduler.add_job(api_handle.StationRealKpi, 'interval', minutes=5, args=[db], id="job_StationRealKpi")
    scheduler.add_job(api_handle.KpiStationHour, 'interval', hours=1, args=[db], id="job_KpiStationHour")
    scheduler.add_job(api_handle.KpiStationDay, 'interval', days=1, args=[db], id="job_KpiStationDay")
    scheduler.add_job(api_handle.KpiStationMonth, 'interval', days=30, args=[db], id="job_KpiStationMonth")
    scheduler.add_job(api_handle.KpiStationYear, 'interval', days=365, args=[db], id="job_KpiStationYear")
    scheduler.start()

""" @router.get("/time/travel")
async def read_data():
    try:
        db: Session = next(get_db())
        for x in range(14,0,-1):
            api_handle.time_travel = x
            api_handle.KpiStationHour(db)
        payload = {}
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
 """