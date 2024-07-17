from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.db import get_db, get_cache, set_cache
from app.report.db import DatabaseHandle

router = APIRouter()

db_handle = DatabaseHandle()

@router.get('/monthly/{station}')
async def station_xlsx(station: int, year: int, month: int):
    db = None
    try:
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        if not (1970 <= year <= 2036):
            raise ValueError("Year must be between 1970 and 2036")
        if station <= 0:
            raise ValueError("Station must be a positive integer")
        this_month = datetime.now().month
        this_year = datetime.now().year
        period_dt = datetime(year, month, 1)
        db: Session = next(get_db())
        
        if this_month <= month and this_year == year:
            report_cache = get_cache(f'report_{datetime.now().strftime("%m_%Y")}_{station}')
        else:
            report_cache = get_cache(f'report_{period_dt.strftime("%m_%Y")}_{station}')
        if report_cache:
            return report_cache

        data = db_handle.get_tou_station(db, period_dt, station)
        if data:
            if this_month <= month and this_year == year:
                set_cache(f'report_{datetime.now().strftime("%m_%Y")}_{station}', data, 86400)  # 1 day
            else:
                set_cache(f'report_{period_dt.strftime("%m_%Y")}_{station}', data, 2592000)  # 30 days
            return data
        else:
            raise ValueError("Station code not found")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: Unable to generate data. {str(e)}")
    finally:
        if db:
            db.close()
