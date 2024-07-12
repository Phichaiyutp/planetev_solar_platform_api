
import time
from app.core.models import MsStations, Tou, Tod, Device, DeviceType, Tariff, StationDay
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)


class DatabaseHandle:
    def __init__(self):
        pass

    def get_tou_station(self, db: Session, _dt: datetime, station_code: int):
        try:
            dt_now = datetime(datetime.now().year, datetime.now().month, 1)
            if _dt > dt_now:
                query_datetime = dt_now.strftime('%Y-%m-%d')
                unixdt_s = time.mktime(dt_now.timetuple())
                shiftmonthly = _dt + timedelta(days=31)
                unixdt_e = time.mktime(shiftmonthly.timetuple())
            else:
                query_datetime = _dt.strftime('%Y-%m-%d')
                unixdt_s = time.mktime(_dt.timetuple())
                shiftmonthly = _dt + timedelta(days=31)
                unixdt_e = time.mktime(shiftmonthly.timetuple())

            station = db.query(MsStations.station_name, MsStations.capacity).filter(
                MsStations.station_code == station_code).first()

            if not station:
                raise ValueError("Station code not found")

            station_day_data = db.query(StationDay.use_power, StationDay.collect_time) \
                .filter(StationDay.collect_time >= unixdt_s,
                        StationDay.collect_time < unixdt_e,
                        StationDay.station_code == station_code) \
                .all()

            station_day = [
                {
                    'use_power': item.use_power,
                    'collect_time': datetime.fromtimestamp(item.collect_time).strftime('%d-%m-%Y %H:%M:%S'),
                }
                for item in station_day_data
            ]

            devices_data = db.query(Device.dev_name, Device.esn_code, Device.exd_warranty, DeviceType.dev_type_name) \
                .join(DeviceType) \
                .filter(Device.station_code == station_code) \
                .all()

            devices = [
                {
                    'name': item.dev_name,
                    'deviceType': item.dev_type_name.capitalize(),
                    'exd_warranty': item.exd_warranty.strftime('%d-%m-%Y') if item.exd_warranty else None
                }
                for item in devices_data
            ]

            tariff = db.query(Tariff.name, Tariff.volt_rate_max, Tariff.dsc, Tariff.ft, Tariff.tou_on_pk_rate_max, Tariff.tou_off_pk_rate_max, Tariff.tod_rate_min, Tariff.tod_rate_mid, Tariff.tod_rate_max) \
                .join(Device) \
                .filter(Device.station_code == station_code, Device.dev_type_id == 1) \
                .first()

            if not tariff:
                raise ValueError("Tariff not found for the station")

            if tariff.name == "TOU_FIX_TIME" or tariff.name == "TOU":

                bill = db.query(Tou).filter(
                    func.DATE_TRUNC('month', Tou.on_date) == query_datetime,
                    Tou.station_code == station_code
                ).order_by(Tou.on_date.asc()).all()

                if not bill:
                    raise ValueError("Bill not found for the station")

                daily = [
                    {
                        'date': item.on_date.strftime('%d-%m-%Y'),
                        'offPeak': item.yield_off_peak if item.yield_off_peak else 0,
                        'onPeak': item.yield_on_peak if item.yield_on_peak else 0,
                        'total': item.yield_total if item.yield_total else 0,
                        'consumption': next((sd['use_power'] for sd in station_day if sd['collect_time'] == item.on_date.strftime('%d-%m-%Y 00:00:00')), 0)
                    }
                    for item in bill
                ]
                offPeak = sum(item['offPeak'] for item in daily)
                onPeak = sum(item['onPeak'] for item in daily)
                offPeakRateDsc = tariff.tou_off_pk_rate_max - (tariff.tou_off_pk_rate_max * tariff.dsc)
                onPeakRateDsc = tariff.tou_on_pk_rate_max - (tariff.tou_on_pk_rate_max * tariff.dsc)
                onPeakAmount = (onPeak * onPeakRateDsc) + (onPeak * tariff.ft)
                offPeakAmount = (offPeak * offPeakRateDsc) + (offPeak * tariff.ft)
                return {
                    'date': datetime.now().strftime('%d-%m-%Y'),
                    'tariff': tariff.name,
                    'project': 'ระบบผลิตไฟฟ้าพลังงานแสงอาทิตย์บนหลังคา (Solar RoofTop Syatem)',
                    'location': station.station_name,
                    'preparedBy': 'Input From Frontend',
                    'capacity': station.capacity,
                    'summaryDateForm': daily[0]['date'] if daily else None,
                    'summaryDateTo': daily[-1]['date'] if daily else None,
                    'voltRate': tariff.volt_rate_max,
                    'discount': f"{tariff.dsc * 100:.0f}%",
                    'ft': tariff.ft,
                    'billPeriod': bill[0].on_date.strftime('%m/%Y') if bill else None,
                    'amount': round(onPeakAmount + offPeakAmount, 2),
                    'offPeak': offPeak,
                    'onPeak': onPeak,
                    'offPeakRate': round(tariff.tou_off_pk_rate_max, 4),
                    'onPeakRate': round(tariff.tou_on_pk_rate_max, 4),
                    'offPeakRateDsc': round(offPeakRateDsc, 4),
                    'onPeakRateDsc': round(onPeakRateDsc, 4),
                    'offPeakAmount': round(offPeakAmount, 2),
                    'onPeakAmount': round(onPeakAmount, 2),
                    'total': round(sum(item['total'] for item in daily), 2),
                    'consumption': round(sum(item['consumption'] for item in daily), 2),
                    'daily': daily,
                    'devices': devices
                }

            elif tariff.name == "TOD":
                bill = db.query(Tod).filter(
                    func.DATE_TRUNC('month', Tod.on_date) == query_datetime,
                    Tod.station_code == station_code
                ).order_by(Tod.on_date.asc()).all()

                if not bill:
                    raise ValueError("Bill not found for the station")

                daily = [
                    {
                        'date': item.on_date.strftime('%d-%m-%Y'),
                        'total': item.yield_total if item.yield_total else 0,
                        'consumption': next((sd['use_power'] for sd in station_day if sd['collect_time'] == item.on_date.strftime('%d-%m-%Y 00:00:00')), 0)
                    }
                    for item in bill
                ]
                total = sum(item['total'] for item in daily)

                eRateMin = tariff.tod_rate_min
                eRateMid = tariff.tod_rate_mid
                eRateMax = tariff.tod_rate_max
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
                if total <= 150:
                    eRateMinTotal = total
                    eRateMinAmount = (eRateMinTotal * eRateMinDsc) + (eRateMinTotal * tariff.ft)
                elif 150 < total <= 400:
                    eRateMinTotal = 150
                    eRateMidTotal = total - 150
                    eRateMinAmount = (150 * eRateMidDsc) + (eRateMinTotal * tariff.ft)
                    eRateMidAmount = (eRateMidTotal * eRateMidDsc) + (eRateMidTotal * tariff.ft)
                elif total > 400:
                    eRateMinTotal = 150
                    eRateMidTotal = 250
                    eRateMaxTotal = total - 250 
                    eRateMinAmount = (eRateMinTotal * eRateMinDsc) + (eRateMinTotal * tariff.ft)
                    eRateMidAmount = (eRateMidTotal * eRateMidDsc) + (eRateMidTotal * tariff.ft)
                    eRateMaxAmount = (eRateMaxTotal * eRateMaxDsc) + (eRateMaxTotal * tariff.ft)

                return {
                    'date': datetime.now().strftime('%d-%m-%Y'),
                    'tariff': tariff.name,
                    'project': 'ระบบผลิตไฟฟ้าพลังงานแสงอาทิตย์บนหลังคา (Solar RoofTop Syatem)',
                    'location': station.station_name,
                    'preparedBy': 'Input From Frontend',
                    'capacity': station.capacity,
                    'summaryDateForm': daily[0]['date'] if daily else None,
                    'summaryDateTo': daily[-1]['date'] if daily else None,
                    'voltRate': tariff.volt_rate_max,
                    'discount': f"{tariff.dsc * 100:.0f}%",
                    'ft': tariff.ft,
                    'billPeriod': bill[0].on_date.strftime('%m/%Y') if bill else None,
                    'amount': round(eRateMinAmount + eRateMidAmount + eRateMaxAmount, 2),
                    'eRateMinTotal' : round(eRateMinTotal, 2),
                    'eRateMidTotal' : round(eRateMidTotal, 2),
                    'eRateMaxTotal' : round(eRateMaxTotal, 2),
                    'eRateMinAmount': round(eRateMinAmount, 2),
                    'eRateMidAmount': round(eRateMidAmount, 2),
                    'eRateMaxAmount': round(eRateMaxAmount, 2),
                    'eRateMin': round(eRateMin, 4),
                    'eRateMid': round(eRateMid, 4),
                    'eRateMax': round(eRateMax, 4),
                    'eRateMinDsc': round(eRateMinDsc, 4),
                    'eRateMidDsc': round(eRateMidDsc, 4),
                    'eRateMaxDsc': round(eRateMaxDsc, 4),
                    'total': round(total, 2),
                    'consumption': round(sum(item['consumption'] for item in daily), 2),
                    'daily': daily,
                    'devices': devices
                }

            else:
                raise ValueError("Unknown tariff type")

        except Exception as e:
            db.rollback()
            logging.error(f"Error: {e}")
            raise
