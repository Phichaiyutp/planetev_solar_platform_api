from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.db import get_db, get_cache, set_cache
from app.report.db import DatabaseHandle

router = APIRouter()

db_handle = DatabaseHandle()

@router.get('/monthly/chart/{id}')
async def chart_report(id: str):
    try:
        cached_data = get_cache(id)
        
        if cached_data is None:
            raise HTTPException(status_code=404, detail="Data not found in cache")

        return cached_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get('/monthly')
async def summary_report(year: int, month: int, station: Optional[str] = None):
    db = None
    try:
        if not (1 <= month <= 12):
            raise Exception("Month must be between 1 and 12")
        if not (1970 <= year <= 2036):
            raise Exception("Year must be between 1970 and 2036")

        this_month = datetime.now().month
        this_year = datetime.now().year
        period_dt = datetime(year, month, 1)
        db: Session = next(get_db())

        cache_key_suffix = station if station else 'all'
        cache_key_current = f'summary_report_{datetime.now().strftime("%m_%Y")}_{
            cache_key_suffix}'
        cache_key_period = f'summary_report_{period_dt.strftime("%m_%Y")}_{
            cache_key_suffix}'

        report_cache = get_cache(
            cache_key_current if this_month <= month and this_year == year else cache_key_period)
        if report_cache:
            return report_cache

        list_of_station = []
        if station:
            list_of_station = [int(x) for x in station.split(',')]

        data = db_handle.get_tariff_summary(db, period_dt, list_of_station)
        if data:
            if not 'error' in data:
                # 1 day or 30 days
                cache_duration = 86400 if this_month <= month and this_year == year else 2592000
                set_cache(cache_key_current if this_month <= month and this_year ==
                    year else cache_key_period, data, cache_duration)
            return data
        else:
            raise Exception("Summary report not found")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error: Unable to generate data. {str(e)}")
    finally:
        if db:
            db.close()


@router.get('/monthly/{station}')
async def station_report(station: int, year: int, month: int):
    db = None
    try:
        if not (1 <= month <= 12):
            raise Exception("Month must be between 1 and 12")
        if not (1970 <= year <= 2036):
            raise Exception("Year must be between 1970 and 2036")
        if station <= 0:
            raise Exception("Station must be a positive integer")
        this_month = datetime.now().month
        this_year = datetime.now().year
        period_dt = datetime(year, month, 1)
        db: Session = next(get_db())

        if this_month <= month and this_year == year:
            report_cache = get_cache(
                f'report_{datetime.now().strftime("%m_%Y")}_{station}')
        else:
            report_cache = get_cache(
                f'report_{period_dt.strftime("%m_%Y")}_{station}')
        if report_cache:
            return report_cache

        data = db_handle.get_tariff_station(db, period_dt, station)
        if data:
            if this_month <= month and this_year == year:
                set_cache(f'report_{datetime.now().strftime("%m_%Y")}_{
                          station}', data, 86400)  # 1 day
            else:
                set_cache(f'report_{period_dt.strftime("%m_%Y")}_{
                          station}', data, 2592000)  # 30 days
            return data
        else:
            raise Exception("Station code not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error: Unable to generate data. {str(e)}")
    finally:
        if db:
            db.close()
