from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
import datetime
from app.core.db import get_db
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

        dt = datetime.datetime(year, month, 1)
        db: Session = next(get_db())
        data = db_handle.get_tou_station(db, dt, station)
        if data:
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
