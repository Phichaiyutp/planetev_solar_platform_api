from datetime import datetime
import json
import re
import requests
from sqlalchemy.orm import Session
from app.core.models import Inverter, Station, Device, StationYear, Tou, Tariff,MsStations,Energy,SensorEnergy,Environment
from app.core.db import get_db
from sqlalchemy.sql import func
from fastapi import APIRouter, Depends, HTTPException
from cachetools.func import ttl_cache

router = APIRouter()

def get_station(db: Session) -> list:
    try:
        # Fetch station data
        ms_stations = db.query(
            MsStations.capacity,
            MsStations.latitude,
            MsStations.longitude,
            MsStations.station_code,
            MsStations.station_name,
            MsStations.station_address
        ).all()
        
        payload = []

        for ms_station in ms_stations:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={ms_station.latitude}&lon={ms_station.longitude}&appid=b547177637945380e8945526d457fc06"
            weather_data = requests.get(url)
            if weather_data.status_code == 200:
                weather = json.loads(weather_data.text)
                cond_id = weather['weather'][0]['id']
                cond_en = weather['weather'][0]['main']
                description = weather['weather'][0]['description']
                tc = weather['main']['temp']/10
                rh = weather['main']['humidity']
                weather_icon = weather['weather'][0]['icon']
                cond_icon = f"https://openweathermap.org/img/wn/{weather_icon}@2x.png"
            else :
                cond_id = 0
                cond_en = "Unknown"
                description = "Unknown"
                tc = 0
                rh = 0
                cond_icon = "Unknown"
            station_name_short = re.sub(r' รหัส \d+', '', ms_station.station_name) if "รหัส" in ms_station.station_name else ms_station.station_name
            station = db.query(Station.day_power, Station.total_power, Station.real_health_state).filter(Station.station_code == ms_station.station_code).first()
            if station.real_health_state == 1 :
                station_status = "Offline"
            elif station.real_health_state == 2 :
                station_status = "Faulty"
            elif station.real_health_state == 3 :
                station_status = "Online"
            else :
                station_status = "Unknown"
            station_year = db.query(StationYear.reduction_total_co2).filter(StationYear.station_code == ms_station.station_code).first()
            realtime_pv_data = db.query(Inverter.station_code, Inverter.active_power,Inverter.total_cap).filter(
                Inverter.station_code == ms_station.station_code
            ).order_by(Inverter.timestamp.desc()).first()
            realtime_pv = realtime_pv_data.active_power if realtime_pv_data and realtime_pv_data.active_power is not None else 0
            energy = realtime_pv_data.total_cap if realtime_pv_data and realtime_pv_data.total_cap is not None else 0
            energy_data = db.query(Energy.station_code, Energy.active_power).filter(
                Energy.station_code == ms_station.station_code
            ).order_by(Energy.timestamp.desc()).first()
            if energy_data :
                realtime_grid = abs(energy_data.active_power) if energy_data and energy_data.active_power is not None else 0
            else:
                sensor_energy_data = db.query(SensorEnergy.station_code, SensorEnergy.active_power).filter(
                    SensorEnergy.station_code == ms_station.station_code
                ).order_by(SensorEnergy.timestamp.desc()).first()
                realtime_grid = abs(sensor_energy_data.active_power) if sensor_energy_data and sensor_energy_data.active_power is not None else 0
            tou_data = db.query(Tou.yield_off_peak, Tou.yield_on_peak, Tou.yield_total).filter(Tou.station_code == ms_station.station_code).all()
            total_on_peak = sum(item.yield_on_peak or 0 for item in tou_data)
            total_off_peak = sum(item.yield_off_peak or 0 for item in tou_data)

            tariff = db.query(Tariff.dsc, Tariff.ft, Tariff.tou_on_pk_rate_max, Tariff.tou_off_pk_rate_max) \
                .filter((Tariff.name == "TOU_FIX_TIME") | (Tariff.name == "TOU")) \
                .first()

            offPeakRateDsc = tariff.tou_off_pk_rate_max - (tariff.tou_off_pk_rate_max * tariff.dsc)
            onPeakRateDsc = tariff.tou_on_pk_rate_max - (tariff.tou_on_pk_rate_max * tariff.dsc)
            revenue_on = (total_on_peak * onPeakRateDsc) + (total_on_peak * tariff.ft)
            revenue_off = (total_off_peak * offPeakRateDsc) + (total_off_peak * tariff.ft)
            revenue_total = revenue_on + revenue_off


            payload.append({
                "timestamp": datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                "station_code": ms_station.station_code,
                "station_status": station_status,
                "co2": station_year.reduction_total_co2,
                "capacity": ms_station.capacity,
                "latitude": ms_station.latitude,
                "longitude": ms_station.longitude,
                "station_name": ms_station.station_name,
                "station_address": ms_station.station_address,
                "station_name_short": station_name_short,
                "condEn": cond_en,
                "condDescription" : description, 
                "cond_id": cond_id,
                "cond_icon" : cond_icon,
                "rh": round(rh, 2),
                "tc": round(tc, 2),
                "realtime_pv": round(realtime_pv, 2),
                "energy": round(energy, 2),
                "yield_today": round(station.day_power, 2),
                "total_yield": round(station.total_power, 2),
                "realtime_grid": round(realtime_grid/1000, 2),
                "total_on_peak": round(total_on_peak, 2),
                "total_off_peak": round(total_off_peak, 2),
                "energy_overall": round(total_on_peak + total_off_peak, 2),
                "revenue_total": round(revenue_total, 2),
                "revenue_on": round(revenue_on, 2),
                "revenue_off": round(revenue_off, 2),
                "realtime_load": round(realtime_pv + realtime_grid, 2),
            })
        return payload
    except Exception as e:
        raise ValueError(f"Get station Error: {e}")
    
def get_overall(db: Session) -> dict:
    try:
        devices = db.query(Device.esn_code).filter(
            Device.dev_type_id == 1
        ).all()

        realtime_pv_all = []
        for device in devices:
            realtime_pv_data = db.query(Inverter.station_code, Inverter.active_power).filter(
                Inverter.sn == device.esn_code).order_by(Inverter.timestamp.desc()).first()
            realtime_pv_all.append({
                'station_code': realtime_pv_data.station_code,
                'realtime_pv': realtime_pv_data.active_power
            })

        realtime_pv = sum(item['realtime_pv'] for item in realtime_pv_all)
        station = db.query(Station.day_power, Station.total_power).all()
        yield_today = sum(item.day_power for item in station)
        total_yield = sum(item.total_power for item in station)
        co_two_data = db.query(StationYear.reduction_total_co2).all()
        co_two = sum(item.reduction_total_co2 for item in co_two_data)
        station_all = db.query(Station.total_power).all()
        # total_string_capacity = sum(item.total_power for item in station_all)
        tou_data = db.query(Tou.yield_off_peak, Tou.yield_on_peak, Tou.yield_total).all()
        total_off_peak = 0
        total_on_peak = 0
        energy_overall = 0
        for item in tou_data:
            total_off_peak += item[0] if item[0] is not None else 0
            total_on_peak += item[1] if item[1] is not None else 0
            energy_overall += item[2] if item[2] is not None else 0

        tariff = db.query(Tariff.dsc, Tariff.ft, Tariff.tou_on_pk_rate_max, Tariff.tou_off_pk_rate_max) \
            .filter((Tariff.name == "TOU_FIX_TIME") | (Tariff.name == "TOU")) \
            .first()

        offPeakRateDsc = tariff.tou_off_pk_rate_max - (tariff.tou_off_pk_rate_max * tariff.dsc)
        onPeakRateDsc = tariff.tou_on_pk_rate_max - (tariff.tou_on_pk_rate_max * tariff.dsc)
        revenue_on = (total_on_peak * onPeakRateDsc) + (total_on_peak * tariff.ft)
        revenue_off = (total_off_peak * offPeakRateDsc) + (total_off_peak * tariff.ft)
        revenue_total = revenue_on + revenue_off

        payload = {
            "timestamp": datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
            "realtime_pv": round(realtime_pv, 2),
            "yield_today": round(yield_today, 2),
            "total_yield": round(total_yield, 2),
            "co2": round(co_two, 2),
            "total_on_peak": round(total_on_peak, 2),
            "total_off_peak": round(total_off_peak, 2),
            "energy_overall": round(energy_overall, 2),
            "revenue_total": round(revenue_total, 2),
            "revenue_on": round(revenue_on, 2),
            "revenue_off": round(revenue_off, 2),
        }
        return payload
    except Exception as e:
        raise ValueError("Get overall Error")

# Configure caching with a TTL (Time To Live) of 300 seconds (5 minutes)
@ttl_cache(maxsize=128, ttl=300)
def cached_get_overall(db: Session) -> dict:
    return get_overall(db)

@ttl_cache(maxsize=128, ttl=300)
def cached_get_station(db: Session) -> dict:
    return get_station(db)

@router.get("/overall")
async def read_data(db: Session = Depends(get_db)):
    try:
        payload = cached_get_overall(db)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error {e}")

@router.get("/station")
async def read_data(db: Session = Depends(get_db)):
    try:
        payload = cached_get_station(db)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error {e}")