from datetime import time
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.fusionsolar.handle import ApiHandle
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = APIRouter()
api_handle = ApiHandle()
scheduler = BackgroundScheduler()
scheduler.start()

scheduler = AsyncIOScheduler()


async def scheduler_callback(db:Session):
    api_handle.DevRealKpi(db)
    api_handle.StationRealKpi(db)
    api_handle.KpiStationHour(db)
    api_handle.KpiStationDay(db)
    api_handle.KpiStationMonth(db)
    api_handle.KpiStationYear(db)

    scheduler.add_job(api_handle.DevRealKpi, trigger='interval', minutes=5, args=[db], id="job_DevRealKpi")
    scheduler.add_job(api_handle.StationRealKpi, trigger='interval', minutes=5, args=[db], id="job_StationRealKpi")
    scheduler.add_job(api_handle.KpiStationHour, trigger='interval', hours=1, args=[db], id="job_KpiStationHour")  
    scheduler.add_job(api_handle.KpiStationDay, trigger='interval', days=1, args=[db], id="job_KpiStationDay")    
    scheduler.add_job(api_handle.KpiStationMonth, trigger='interval', days=30, args=[db], id="job_KpiStationMonth") 
    scheduler.add_job(api_handle.KpiStationYear, trigger='interval', days=365, args=[db], id="job_KpiStationYear")  

    if not scheduler.running:
        scheduler.start()

@router.get("/time/travel")
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
