
import time
from typing import List, Optional
from app.core.models import MsStations, Tou, Tod, Device, DeviceType, Tariff, StationDay
from app.core.db import get_db, get_cache, set_cache
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pendulum
import logging

import matplotlib.pyplot as plt
import base64
from io import BytesIO
import json

logging.basicConfig(level=logging.INFO)


class DatabaseHandle:
    def __init__(self):
        pass

    def get_tariff_summary(self, db: Session, period_dt: datetime, stations: Optional[List[int]] = None):
        try:
            stations_data = []
            error = []

            # Determine the period for the report
            this_month = datetime(datetime.now().year, datetime.now().month, 1)
            if period_dt > this_month:
                this_period = this_month
                end_day = datetime.now()
                dt_s = this_month
                dt_e = pendulum.instance(this_month).add(months=1)
            else:
                this_period = period_dt
                end_day = pendulum.instance(period_dt).add(
                    months=1).subtract(days=1)
                dt_s = period_dt
                dt_e = pendulum.instance(period_dt).add(months=1)

            # Thai month names
            months_th = {
                1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน", 5: "พฤษภาคม", 6: "มิถุนายน",
                7: "กรกฎาคม", 8: "สิงหาคม", 9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"
            }

            # Query tariff information
            tariff_query = db.query(
                Device.station_code,
                Tariff.name,
                Tariff.volt_rate_max,
                Tariff.dsc,
                Tariff.ft,
                Tariff.tou_on_pk_rate_max,
                Tariff.tou_off_pk_rate_max,
                Tariff.tod_rate_min,
                Tariff.tod_rate_mid,
                Tariff.tod_rate_max,
                Tariff.tod_rate_min,
                Tariff.tod_rate_mid,
                Tariff.tod_rate_max
            ).join(Device).filter(Device.dev_type_id == 1)

            # Check and filter by stations
            if stations:
                for station in stations:
                    ms_station = db.query(MsStations).filter(
                        MsStations.station_code == station).first()
                    if not ms_station:
                        error.append(
                            {'msg': f'Station code {station} not found'})
                tariff_query = tariff_query.filter(
                    Device.station_code.in_(stations))

            tariffs = tariff_query.all()

            if not tariffs:
                error.append(
                    {'msg': 'No tariffs found for the specified stations.'})
                return self.prepare_payload(this_period, end_day, months_th, stations_data, error)

            for tariff_item in tariffs:
                ms_station = db.query(MsStations.station_name).filter(
                    MsStations.station_code == tariff_item.station_code).first()

                amount = 0.0

                if tariff_item.name in ["TOU_FIX_TIME", "TOU"]:
                    tou = db.query(
                        Tou.station_code,
                        func.sum(Tou.yield_off_peak).label('yield_off_peak'),
                        func.sum(Tou.yield_on_peak).label('yield_on_peak'),
                        func.sum(Tou.yield_total).label('yield_total')
                    ).filter(
                        Tou.on_date >= dt_s,
                        Tou.on_date < dt_e,
                        Tou.station_code == tariff_item.station_code
                    ).group_by(Tou.station_code).first()

                    if not tou:
                        error.append({'msg': f'Bill not found for the station with code {
                            tariff_item.station_code}'})
                        continue

                    total_yield = tou.yield_total
                    offPeak = tou.yield_off_peak
                    onPeak = tou.yield_on_peak
                    offPeakRateDsc = tariff_item.tou_off_pk_rate_max - \
                        (tariff_item.tou_off_pk_rate_max * tariff_item.dsc)
                    onPeakRateDsc = tariff_item.tou_on_pk_rate_max - \
                        (tariff_item.tou_on_pk_rate_max * tariff_item.dsc)
                    onPeakAmount = (onPeak * onPeakRateDsc) + \
                        (onPeak * tariff_item.ft)
                    offPeakAmount = (offPeak * offPeakRateDsc) + \
                                    (offPeak * tariff_item.ft)
                    amount = onPeakAmount + offPeakAmount

                if tariff_item.name in ["TOD"]:
                    tod = db.query(
                        Tod.station_code,
                        func.sum(Tod.yield_total).label('yield_total')
                    ).filter(
                        Tod.on_date >= dt_s,
                        Tod.on_date < dt_e,
                        Tod.station_code == tariff_item.station_code
                    ).group_by(Tod.station_code).first()

                    if not tod:
                        error.append({'msg': f'Bill not found for the station with code {
                            tariff_item.station_code}'})
                        continue
                    total_yield = tod.yield_total
                    eRateMin = tariff_item.tod_rate_min
                    eRateMid = tariff_item.tod_rate_mid
                    eRateMax = tariff_item.tod_rate_max
                    eRateMinDsc = round(eRateMin -
                                        (eRateMin * tariff_item.dsc), 4)
                    eRateMidDsc = round(eRateMid -
                                        (eRateMid * tariff_item.dsc), 4)
                    eRateMaxDsc = round(eRateMax -
                                        (eRateMax * tariff_item.dsc), 4)
                    eRateMinTotal = 0
                    eRateMidTotal = 0
                    eRateMaxTotal = 0
                    eRateMinAmount = 0
                    eRateMidAmount = 0
                    eRateMaxAmount = 0
                    if total_yield <= 150:
                        eRateMinTotal = total_yield
                        eRateMinAmount = (eRateMinTotal * eRateMinDsc) + \
                            (eRateMinTotal * tariff_item.ft)
                    elif 150 < total_yield <= 400:
                        eRateMinTotal = 150
                        eRateMidTotal = total_yield - 150
                        eRateMinAmount = (150 * eRateMidDsc) + \
                            (eRateMinTotal * tariff_item.ft)
                        eRateMidAmount = (eRateMidTotal * eRateMidDsc) + \
                            (eRateMidTotal * tariff_item.ft)
                    elif total_yield > 400:
                        eRateMinTotal = 150
                        eRateMidTotal = 250
                        eRateMaxTotal = total_yield - 250
                        eRateMinAmount = (eRateMinTotal * eRateMinDsc) + \
                            (eRateMinTotal * tariff_item.ft)
                        eRateMidAmount = (eRateMidTotal * eRateMidDsc) + \
                            (eRateMidTotal * tariff_item.ft)
                        eRateMaxAmount = (eRateMaxTotal * eRateMaxDsc) + \
                            (eRateMaxTotal * tariff_item.ft)

                    amount = eRateMinAmount + eRateMidAmount + eRateMaxAmount

                stations_data.append({
                    'stationId': tariff_item.station_code,
                    'name': ms_station.station_name if ms_station else 'Unknown',
                    'yield': round(total_yield, 2),
                    'amount': round(amount, 2),
                    'details': self.get_tariff_station(db, period_dt, tariff_item.station_code)
                })

            return self.prepare_payload(this_period, end_day, months_th, stations_data, error)

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"SQLAlchemy Error: {e}")
            return {'error': 'Database error occurred.'}
        except Exception as e:
            logging.error(f"General Error: {e}")
            return {'error': 'An unexpected error occurred.'}

    def prepare_payload(self, this_period, end_day, months_th, stations_data, error):
        payload = {
            "billPeriod": f"ประจำเดือน {months_th[this_period.month]} {this_period.year}",
            'summaryDateForm': f"{this_period.day} {months_th[this_period.month]} {this_period.year}",
            'summaryDateTo': f"{end_day.day} {months_th[this_period.month]} {this_period.year}",
            'stations': stations_data
        }
        if error:
            payload['error'] = error
        return payload

    def get_tariff_station(self, db: Session, period_dt: datetime, station_code: int):
        try:
            this_month = datetime(datetime.now().year, datetime.now().month, 1)
            if period_dt > this_month:
                query_datetime, chart_datetime, dt_s, unixdt_s, dt_e, unixdt_e = self.get_date_ranges(
                    this_month)
            else:
                query_datetime, chart_datetime, dt_s, unixdt_s, dt_e, unixdt_e = self.get_date_ranges(
                    period_dt, this_month)

            station = self.get_station_info(db, station_code)
            station_day = self.get_station_day_data(
                db, unixdt_s, unixdt_e, station_code)
            devices = self.get_devices_data(db, station_code)
            tariff = self.get_tariff_info(db, station_code)
            tariff_payload = {}

            if tariff.name in ["TOU_FIX_TIME", "TOU"]:
                daily, tou_payload, bill_period = self.handle_tou_tariff(
                    db, dt_s, dt_e, station_code, station_day, tariff)
                tariff_payload = tou_payload
            elif tariff.name == "TOD":
                daily, tod_payload, bill_period = self.handle_tod_tariff(
                    db, dt_s, dt_e, station_code, station_day, tariff)
                tariff_payload = tod_payload
            else:
                raise Exception("Unknown tariff type")

            img_base64 = self.generate_chart(
                daily, station_code, chart_datetime)

            payload = self.create_payload(
                tariff_payload,
                daily,
                tariff,
                station,
                devices,
                img_base64,
                chart_datetime,
                bill_period,
                station_code
            )

            return payload

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"SQLAlchemy Error: {e}")
        except Exception as e:
            logging.error(f"Error: {e}")

    def get_date_ranges(self, period_dt, this_month=None):
        if not this_month:
            this_month = datetime(datetime.now().year, datetime.now().month, 1)
        query_datetime = period_dt.strftime('%Y-%m-%d')
        chart_datetime = this_month.strftime('%Y_%m')
        dt_s = period_dt
        unixdt_s = time.mktime(period_dt.timetuple())
        shiftmonthly = pendulum.instance(period_dt).add(months=1)
        dt_e = shiftmonthly
        unixdt_e = time.mktime(shiftmonthly.timetuple())
        return query_datetime, chart_datetime, dt_s, unixdt_s, dt_e, unixdt_e

    def get_station_info(self, db, station_code):
        station = db.query(MsStations.station_name, MsStations.capacity).filter(
            MsStations.station_code == station_code).first()
        if not station:
            raise Exception("Station code not found")
        return station

    def get_station_day_data(self, db, unixdt_s, unixdt_e, station_code):
        station_day_data = db.query(StationDay.use_power, StationDay.collect_time)\
            .filter(StationDay.collect_time >= unixdt_s, StationDay.collect_time < unixdt_e, StationDay.station_code == station_code).all()
        station_day = [
            {
                'use_power': item.use_power,
                'timestamp': datetime.fromtimestamp(item.collect_time).strftime('%d-%m-%Y %H:%M:%S'),
            }
            for item in station_day_data
        ]
        return station_day

    def get_devices_data(self, db, station_code):
        devices_data = db.query(Device.dev_name, Device.esn_code, Device.exd_warranty, DeviceType.dev_type_name)\
            .join(DeviceType)\
            .filter(Device.station_code == station_code).all()
        devices = [
            {
                'name': item.dev_name,
                'deviceType': item.dev_type_name.capitalize(),
                'exd_warranty': item.exd_warranty.strftime('%d-%m-%Y') if item.exd_warranty else None
            }
            for item in devices_data
        ]
        return devices

    def get_tariff_info(self, db, station_code):
        tariff = db.query(Tariff.name, Tariff.volt_rate_max, Tariff.dsc, Tariff.ft, Tariff.tou_on_pk_rate_max, Tariff.tou_off_pk_rate_max, Tariff.tod_rate_min, Tariff.tod_rate_mid, Tariff.tod_rate_max)\
            .join(Device)\
            .filter(Device.station_code == station_code, Device.dev_type_id == 1).first()
        if not tariff:
            raise Exception("Tariff not found for the station")
        return tariff

    def handle_tou_tariff(self, db, dt_s, dt_e, station_code, station_day, tariff):
        bill = db.query(Tou).filter(Tou.on_date >= dt_s, Tou.on_date < dt_e,
                                    Tou.station_code == station_code).order_by(Tou.on_date.asc()).all()
        if not bill:
            raise Exception("Bill not found for the station")
        daily = [
            {
                'date': item.on_date.strftime('%d-%m-%Y'),
                'offPeak': round(item.yield_off_peak, 2) if item.yield_off_peak else 0,
                'onPeak': round(item.yield_on_peak, 2) if item.yield_on_peak else 0,
                'total': round(item.yield_total, 2) if item.yield_total else 0,
                'consumption': next((round(sd['use_power'], 2) for sd in station_day if sd['timestamp'] == item.on_date.strftime('%d-%m-%Y 00:00:00')), 0)
            }
            for item in bill
        ]

        offPeak = sum(item['offPeak'] for item in daily)
        onPeak = sum(item['onPeak'] for item in daily)
        offPeakRateDsc = tariff.tou_off_pk_rate_max - \
            (tariff.tou_off_pk_rate_max * tariff.dsc)
        onPeakRateDsc = tariff.tou_on_pk_rate_max - \
            (tariff.tou_on_pk_rate_max * tariff.dsc)
        onPeakAmount = (onPeak * onPeakRateDsc) + (onPeak * tariff.ft)
        offPeakAmount = (offPeak * offPeakRateDsc) + (offPeak * tariff.ft)
        bill_period = bill[0].on_date.strftime('%m/%Y') if bill else None
        tou_payload = {
            'amount': round(onPeakAmount + offPeakAmount, 2),
            'offPeak': offPeak,
            'onPeak': onPeak,
            'offPeakRate': round(tariff.tou_off_pk_rate_max, 4),
            'onPeakRate': round(tariff.tou_on_pk_rate_max, 4),
            'offPeakRateDsc': round(offPeakRateDsc, 4),
            'onPeakRateDsc': round(onPeakRateDsc, 4),
            'offPeakAmount': round(offPeakAmount, 2),
            'onPeakAmount': round(onPeakAmount, 2),
        }

        return daily, tou_payload, bill_period

    def handle_tod_tariff(self, db, dt_s, dt_e, station_code, station_day, tariff):
        bill = db.query(Tod).filter(Tod.on_date >= dt_s, Tod.on_date < dt_e,
                                    Tod.station_code == station_code).order_by(Tod.on_date.asc()).all()
        if not bill:
            raise Exception("Bill not found for the station")
        daily = [
            {
                'date': item.on_date.strftime('%d-%m-%Y'),
                'total': round(item.yield_total, 2) if item.yield_total else 0,
                'consumption': next((round(sd['use_power'], 2) for sd in station_day if sd['timestamp'] == item.on_date.strftime('%d-%m-%Y 00:00:00')), 0)
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
        eRateMinTotal, eRateMidTotal, eRateMaxTotal = 0, 0, 0
        eRateMinAmount, eRateMidAmount, eRateMaxAmount = 0, 0, 0
        if total <= 150:
            eRateMinTotal = total
            eRateMinAmount = (eRateMinTotal * eRateMinDsc) + \
                (eRateMinTotal * tariff.ft)
        elif 150 < total <= 400:
            eRateMinTotal = 150
            eRateMidTotal = total - 150
            eRateMinAmount = (150 * eRateMinDsc) + (eRateMinTotal * tariff.ft)
            eRateMidAmount = (eRateMidTotal * eRateMidDsc) + \
                (eRateMidTotal * tariff.ft)
        elif total > 400:
            eRateMinTotal = 150
            eRateMidTotal = 250
            eRateMaxTotal = total - 250
            eRateMinAmount = (eRateMinTotal * eRateMinDsc) + \
                (eRateMinTotal * tariff.ft)
            eRateMidAmount = (eRateMidTotal * eRateMidDsc) + \
                (eRateMidTotal * tariff.ft)
            eRateMaxAmount = (eRateMaxTotal * eRateMaxDsc) + \
                (eRateMaxTotal * tariff.ft)
        bill_period = bill[0].on_date.strftime('%m/%Y') if bill else None
        tod_payload = {
            'amount': round(eRateMinAmount + eRateMidAmount + eRateMaxAmount, 2),
            'eRateMinTotal': round(eRateMinTotal, 2),
            'eRateMidTotal': round(eRateMidTotal, 2),
            'eRateMaxTotal': round(eRateMaxTotal, 2),
            'eRateMinAmount': round(eRateMinAmount, 2),
            'eRateMidAmount': round(eRateMidAmount, 2),
            'eRateMaxAmount': round(eRateMaxAmount, 2),
            'eRateMin': round(eRateMin, 4),
            'eRateMid': round(eRateMid, 4),
            'eRateMax': round(eRateMax, 4),
            'eRateMinDsc': round(eRateMinDsc, 4),
            'eRateMidDsc': round(eRateMidDsc, 4),
            'eRateMaxDsc': round(eRateMaxDsc, 4),
        }

        return daily, tod_payload, bill_period

    def generate_chart(self, daily, station_code, chart_datetime):
        dates = [item['date'] for item in daily]
        totals = [item['total'] for item in daily]
        consumptions = [item['consumption'] for item in daily]
        # Convert dates to datetime objects
        dates = [datetime.strptime(date, '%d-%m-%Y') for date in dates]

        # Plotting
        plt.figure(figsize=(10, 5))
        plt.plot(dates, totals, label='PV output (kWh)',
                 color='blue', marker='o')
        plt.plot(dates, consumptions, label='Total consumption (kWh)',
                 color='orange', marker='o')
        plt.xlabel('Day/Month/Year')
        plt.ylabel('kWh')
        plt.title('Daily Report')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        bottom, top = plt.ylim()
        plt.ylim(top=top+(top*0.1))
        # Adding annotations
        for i, (date, total) in enumerate(zip(dates, totals)):
            plt.annotate(f'{total}', (date, total), textcoords="offset points", xytext=(
                0, 5), ha='center', va='bottom', fontsize=8, rotation=45)

        for i, (date, consumption) in enumerate(zip(dates, consumptions)):
            plt.annotate(f'{consumption}', (date, consumption), textcoords="offset points", xytext=(
                0, 5), ha='center', va='bottom', fontsize=8, rotation=45)

        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        set_cache(f"chart_{station_code}_{chart_datetime}", img_base64, 3000)
        buffer.close()
        return img_base64

    def create_payload(self, tariff_payload, daily, tariff, station, devices, img_base64, chart_datetime, bill_period, station_code):
        payload = {
            'date': datetime.now().strftime('%d-%m-%Y'),
            'tariff': tariff.name,
            'peopleInvolved':{
                'eng' : "Planetcomm Co,Ltd.",
                'pm' : "Planetcomm Co,Ltd.",
                'inspector' : "CJ. Express Group Co,Ltd."
            },
            'project': 'ระบบผลิตไฟฟ้าพลังงานแสงอาทิตย์บนหลังคา (Solar RoofTop Syatem)',
            'location': station.station_name,
            'preparedBy': 'Input From Frontend',
            'capacity': round(station.capacity, 2),
            'summaryDateForm': daily[0]['date'] if daily else None,
            'summaryDateTo': daily[-1]['date'] if daily else None,
            'voltRate': tariff.volt_rate_max,
            'discount': f"{tariff.dsc * 100:.0f}%",
            'ft': round(tariff.ft, 4),
            'billPeriod': bill_period,
            'total': round(sum(item['total'] for item in daily), 2),
            'consumption': round(sum(item['consumption'] for item in daily), 2),
            **tariff_payload,
            'daily': daily,
            'devices': devices,
            'chartEndpoint': f"/api/report/monthly/chart/chart_{station_code}_{chart_datetime}"
        }
        return payload
