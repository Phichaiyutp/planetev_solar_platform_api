import json
import os
import logging
from datetime import datetime, time, timedelta
from sqlalchemy import extract, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.core.db import get_db
from app.core.models import Device, Config, Inverter, Tou, Tariff, Tod, StationHour

logging.basicConfig(level=logging.INFO)
load_dotenv()


class DatabaseHandle:
    def __init__(self):
        self.time_travel = 0

    def get_device(self, db: Session):
        try:
            devices = db.query(Device.esn_code, Tariff.name, Device.station_code).join(Device).filter(
                Device.dev_type_id == 1
            ).all()

            payload = [
                {
                    "esn_code": device[0],
                    "tariff_type": device[1] if device[1] else "TOU_FIX_TIME",
                    "station_code": device[2]
                }
                for device in devices
            ]

            return payload
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error selecting location: {e}")

    def get_tariff(self, db: Session):
        try:
            payload = {
                "TOU_FIX_TIME": {
                    "tou_off_pk_cost_max": 0,
                    "tou_on_pk_cost_max": 0,
                    "dsc": 0,
                    "ft": 0,
                    "tou_on_pk_time_from": "",
                    "tou_on_pk_time_to": "",
                    "tou_off_pk_time_from": "",
                    "tou_off_pk_time_to": "",
                },
                "TOU": {
                    "tou_off_pk_cost_max": 0,
                    "tou_on_pk_cost_max": 0,
                    "dsc": 0,
                    "ft": 0,
                    "tou_on_pk_time_from": "",
                    "tou_on_pk_time_to": "",
                    "tou_off_pk_time_from": "",
                    "tou_off_pk_time_to": "",
                },
                "TOD": {
                    "tod_cost_max": 0,
                    "dsc": 0,
                    "ft": 0,
                },
            }

            # Fetching TOU_FIX_TIME tariff
            tou_fix_time = db.query(Tariff).filter(
                Tariff.name == 'TOU_FIX_TIME').first()
            if tou_fix_time:
                payload["TOU_FIX_TIME"]["tou_off_pk_cost_max"] = tou_fix_time.tou_off_pk_cost_max
                payload["TOU_FIX_TIME"]["tou_on_pk_cost_max"] = tou_fix_time.tou_on_pk_cost_max
                payload["TOU_FIX_TIME"]["dsc"] = tou_fix_time.dsc
                payload["TOU_FIX_TIME"]["ft"] = tou_fix_time.ft
                payload["TOU_FIX_TIME"]["tou_on_pk_time_from"] = tou_fix_time.tou_on_pk_time_from
                payload["TOU_FIX_TIME"]["tou_on_pk_time_to"] = tou_fix_time.tou_on_pk_time_to
                payload["TOU_FIX_TIME"]["tou_off_pk_time_from"] = tou_fix_time.tou_off_pk_time_from
                payload["TOU_FIX_TIME"]["tou_off_pk_time_to"] = tou_fix_time.tou_off_pk_time_to

            # Fetching TOU tariff
            tou = db.query(Tariff).filter(Tariff.name == 'TOU').first()
            if tou:
                payload["TOU"]["tou_off_pk_cost_max"] = tou.tou_off_pk_cost_max
                payload["TOU"]["tou_on_pk_cost_max"] = tou.tou_on_pk_cost_max
                payload["TOU"]["dsc"] = tou.dsc
                payload["TOU"]["ft"] = tou.ft
                payload["TOU"]["tou_on_pk_time_from"] = tou.tou_on_pk_time_from
                payload["TOU"]["tou_on_pk_time_to"] = tou.tou_on_pk_time_to
                payload["TOU"]["tou_off_pk_time_from"] = tou.tou_off_pk_time_from
                payload["TOU"]["tou_off_pk_time_to"] = tou.tou_off_pk_time_to

            # Fetching TOD tariff
            tod = db.query(Tariff).filter(Tariff.name == 'TOD').first()
            if tod:
                payload["TOD"]["tod_cost_max"] = tod.tod_cost_max
                payload["TOD"]["dsc"] = tod.dsc
                payload["TOD"]["ft"] = tod.ft

            return payload
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error selecting location: {e}")

    def get_station_code(self, sn, db: Session):
        try:
            devices = db.query(Device.station_code).filter(
                Device.esn_code == sn).first()

            if devices is not None and devices.station_code is not None:
                payload = devices.station_code
            else:
                payload = None
            return payload
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error getting station code: {e}")

    def insert_tou_fix_time(self, db: Session, station_code):
        try:
            today = datetime.now() - timedelta(days=self.time_travel)
            yesterday = today - timedelta(days=1)
            on_date = f'{yesterday.year}-{yesterday.month}-{yesterday.day}'
            t0 = int(yesterday.replace(hour=0, minute=0, second=0).timestamp())
            t1 = int(yesterday.replace(
                hour=8, minute=59, second=59).timestamp())
            t2 = int(yesterday.replace(
                hour=22, minute=0, second=0).timestamp())
            t3 = int(yesterday.replace(
                hour=23, minute=59, second=59).timestamp())

            morning_off_peak_data = db.query(StationHour.inverter_power).filter(
                StationHour.station_code == station_code,
                StationHour.collect_time.between(t0, t1)
            ).all()
            if not morning_off_peak_data:
                raise ValueError("insert_tou_fix_time morning_off_peak_data not found")
            lunch_on_peak_data = db.query(StationHour.inverter_power).filter(
                StationHour.station_code == station_code,
                StationHour.collect_time.between(t1, t2)
            ).all()
            if not lunch_on_peak_data:
                raise ValueError("lunch_on_peak_data not found")
            dinner_off_peak_data = db.query(StationHour.inverter_power).filter(
                StationHour.station_code == station_code,
                StationHour.collect_time.between(t2, t3)
            ).all()
            if not dinner_off_peak_data:
                raise ValueError("dinner_off_peak_data not found")

            morning_off_peak = (
                sum(item.inverter_power or 0 for item in morning_off_peak_data))
            on_peak = (
                sum(item.inverter_power or 0 for item in lunch_on_peak_data))
            dinner_off_peak = (
                sum(item.inverter_power or 0 for item in dinner_off_peak_data))
            off_peak = morning_off_peak + dinner_off_peak
            yield_total = on_peak + off_peak

            tariff = db.query(Tariff.dsc, Tariff.ft, Tariff.tou_on_pk_rate_max, Tariff.tou_off_pk_rate_max) \
                .filter((Tariff.name == "TOU_FIX_TIME") | (Tariff.name == "TOU")) \
                .first()

            offPeakRateDsc = tariff.tou_off_pk_rate_max - \
                (tariff.tou_off_pk_rate_max * tariff.dsc)
            onPeakRateDsc = tariff.tou_on_pk_rate_max - \
                (tariff.tou_on_pk_rate_max * tariff.dsc)
            revenue_on = (on_peak * onPeakRateDsc) + (on_peak * tariff.ft)
            revenue_off = (off_peak * offPeakRateDsc) + (off_peak * tariff.ft)
            revenue = revenue_on + revenue_off

            tou_exists = db.query(Tou).filter(
                Tou.on_date == on_date,
                Tou.station_code == station_code
            ).first()
            if not tou_exists:
                tou_entry = Tou(on_date=on_date, yield_off_peak=off_peak, yield_on_peak=on_peak,
                                yield_total=yield_total, revenue=revenue, station_code=station_code)
                db.add(tou_entry)
                db.commit()

        except Exception as e:
            db.rollback()
            logging.error(f"Error: {e}")

    def insert_tod(self, db: Session, station_code):
        try:
            today = datetime.now() - timedelta(days=self.time_travel)
            yesterday = today - timedelta(days=1)
            on_date = f'{yesterday.year}-{yesterday.month}-{yesterday.day}'
            t0 = int(yesterday.replace(hour=0, minute=0, second=0).timestamp())
            t3 = int(yesterday.replace(
                hour=23, minute=59, second=59).timestamp())

            station_hour = db.query(StationHour.inverter_power).filter(
                StationHour.station_code == station_code,
                StationHour.collect_time.between(t0, t3)
            ).all()
            if not station_hour:
                raise ValueError("insert_tod yield_total not found")
            
            yield_total = (sum(item.inverter_power or 0 for item in station_hour))


            tariff = db.query(Tariff.dsc, Tariff.ft, Tariff.tod_rate_min, Tariff.tod_rate_mid, Tariff.tod_rate_max) \
                .filter(Tariff.name == "TOD") \
                .first()
            
            eRateMinDsc = round(tariff.tod_rate_min -
                                (tariff.tod_rate_min * tariff.dsc), 4)
            eRateMidDsc = round(tariff.tod_rate_mid -
                                (tariff.tod_rate_mid * tariff.dsc), 4)
            eRateMaxDsc = round(tariff.tod_rate_max -
                                (tariff.tod_rate_max * tariff.dsc), 4)
            eRateMinTotal = 0
            eRateMidTotal = 0
            eRateMaxTotal = 0
            eRateMinAmount = 0
            eRateMidAmount = 0
            eRateMaxAmount = 0

            if yield_total <= 150:
                eRateMinTotal = yield_total
                eRateMinAmount = (eRateMinTotal * eRateMinDsc) + (eRateMinTotal * tariff.ft)
            elif 150 < yield_total <= 400:
                eRateMinTotal = 150
                eRateMidTotal = yield_total - 150
                eRateMinAmount = (150 * eRateMidDsc) + (eRateMinTotal * tariff.ft)
                eRateMidAmount = (eRateMidTotal * eRateMidDsc) + (eRateMidTotal * tariff.ft)
            elif yield_total > 400:
                eRateMinTotal = 150
                eRateMidTotal = 250
                eRateMaxTotal = yield_total - 250 
                eRateMinAmount = (eRateMinTotal * eRateMinDsc) + (eRateMinTotal * tariff.ft)
                eRateMidAmount = (eRateMidTotal * eRateMidDsc) + (eRateMidTotal * tariff.ft)
                eRateMaxAmount = (eRateMaxTotal * eRateMaxDsc) + (eRateMaxTotal * tariff.ft)
            revenue = eRateMinAmount + eRateMidAmount + eRateMaxAmount
            tod_exists = db.query(Tod).filter(
                Tod.on_date == on_date,
                Tod.station_code == station_code
            ).first()

            if not tod_exists:
                tod_entry = Tod(on_date=on_date, yield_total=yield_total ,revenue =revenue, station_code=station_code)
                db.add(tod_entry)
                db.commit()

        except Exception as e:
            db.rollback()
            logging.error(f"Error: {e}")

    def close_db(self, db: Session):
        db.close()
