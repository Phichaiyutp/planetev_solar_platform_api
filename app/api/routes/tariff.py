from fastapi import APIRouter, HTTPException
from enum import Enum
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.tariff.db import DatabaseHandle
from apscheduler.schedulers.background import BackgroundScheduler

router = APIRouter()

time = {
    "t0hh" : 0,
    "t0mm" : 35, # Start counting off-peak in the morning
    "t1hh" : 9,
    "t1mm" : 35, # Summary off-peak in the morning
    "t2hh" : 22,
    "t2mm" : 35, # Summary on-peak   
    "ynp_hh" : 22, 
    "ynp_mm" : 40,  # Summary Yield_On_Peak
    "yfp_hh" : 0, 
    "yfp_mm" : 40,   # Summary Yield_Off_Peak
}

db_handle = DatabaseHandle()
scheduler = BackgroundScheduler()
scheduler.start()

async def scheduler_callback(db:Session):
    device_list = db_handle.get_device(db)
    tariff(device_list,db)

    if not scheduler.running:
        scheduler.start()

def tariff(device_list: dict,db:Session) -> dict:
    for element in device_list:
        if element['tariff_type'] == "TOU_FIX_TIME":
            scheduler.add_job(db_handle.insert_tou_fix_time, trigger='cron', args=[db,element['station_code']], day_of_week='*', hour=time['t0hh'], minute=time['t0mm'], id=f"job_{element['esn_code']}_insert_tou_fix_time")
        
        elif element['tariff_type'] == "TOU":
            pass
            """ scheduler.add_job(db_handle.insert_t0, trigger='cron', args=[db,element['esn_code']], day_of_week='mon-sun', hour=time['t0hh'], minute=time['t0mm'], id=f"job_{element['esn_code']}_insert_t0")
            scheduler.add_job(db_handle.update_yield_off_peak_allday, trigger='cron', args=[db,element['esn_code']], day_of_week='mon,sun', hour=time['yfp_hh'], minute=time['yfp_mm'], id=f"job_{element['esn_code']}_update_yield_off_peak_allday")
            scheduler.add_job(db_handle.update_yield_off_peak, trigger='cron', args=[db,element['esn_code']], day_of_week='tue-sat', hour=time['yfp_hh'], minute=time['yfp_mm'], id=f"job_{element['esn_code']}_update_yield_off_peak")
            scheduler.add_job(db_handle.update_t1, trigger='cron', args=[db,element['esn_code']], day_of_week='mon-fri', hour=time['t1hh'], minute=time['t1mm'], id=f"job_{element['esn_code']}_update_t1")
            scheduler.add_job(db_handle.update_t2, trigger='cron', args=[db,element['esn_code']], day_of_week='mon-sun', hour=time['t2hh'], minute=time['t2mm'], id=f"job_{element['esn_code']}_update_t2")
            scheduler.add_job(db_handle.update_yield_on_peak, trigger='cron', args=[db,element['esn_code']], day_of_week='mon-fri', hour=time['ynp_hh'], minute=time['ynp_mm'], id=f"job_{element['esn_code']}_update_yield_on_peak")
        """
        elif element['tariff_type'] == "TOD":
            scheduler.add_job(db_handle.insert_tod, trigger='cron', args=[db,element['esn_code']], day_of_week='*', hour=0, minute=0, second=0, id=f"job_{element['esn_code']}_tod_total_cap")


@router.get("/time/travel")
async def toufix():
    try:
        db: Session = next(get_db())
        device_list = db_handle.get_device(db)
        for x in range(100,160,1):
            db_handle.time_travel = x
            for element in device_list:
                if element['tariff_type'] == "TOU_FIX_TIME":
                    #db_handle.insert_tou_fix_time(db,element['station_code'])
                    pass
                elif element['tariff_type'] == "TOD":
                    db_handle.insert_tod(db,element['station_code'])
                

        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")        
    