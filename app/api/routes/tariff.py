import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.tariff.db import DatabaseHandle
from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = APIRouter()

time = {
    "t0hh": 0,
    "t0mm": 35,  # Start counting off-peak in the morning
    "t1hh": 9,
    "t1mm": 35,  # Summary off-peak in the morning
    "t2hh": 22,
    "t2mm": 35,  # Summary on-peak
    "ynp_hh": 22,
    "ynp_mm": 40,  # Summary Yield_On_Peak
    "yfp_hh": 0,
    "yfp_mm": 40,  # Summary Yield_Off_Peak
}

db_handle = DatabaseHandle()
scheduler = AsyncIOScheduler()

async def setup_scheduler(db: Session):
    device_list = db_handle.get_device(db)
    for index, element in enumerate(device_list):
        job_id = f"job_{index}_{element['station_code']}"
        args = [db, element['station_code']]
        
        logging.info(f"Scheduling job {job_id} with args: {args}")
        
        if element['tariff_type'] == "TOU_FIX_TIME":
            scheduler.add_job(
                db_handle.insert_tou_fix_time,
                trigger='interval',
                days=1,
                args=args,
                id=job_id
            )
        elif element['tariff_type'] == "TOU":
            scheduler.add_job(
                db_handle.insert_tou_fix_time,
                trigger='interval',
                days=1,
                args=args,
                id=job_id
            )
        elif element['tariff_type'] == "TOD":
            scheduler.add_job(
                db_handle.insert_tod,
                trigger='interval',
                days=1,
                args=args,
                id=job_id
            )
    scheduler.start()
    
""" @router.get("/time/travel")
async def toufix():
    try:
        db: Session = next(get_db())
        device_list = db_handle.get_device(db)
        for x in range(100, 160, 1):
            db_handle.time_travel = x
            for element in device_list:
                if element['tariff_type'] == "TOU_FIX_TIME":
                    # Uncomment if needed
                    # db_handle.insert_tou_fix_time(db, element['station_code'])
                    pass
                elif element['tariff_type'] == "TOD":
                    db_handle.insert_tod(db, element['station_code'])

        return {}
    except Exception as e:
        logging.error(f"Error in /time/travel endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error") """
