import logging
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.core.models import Device, Inverter, Energy, SensorEnergy, Station, MsStations, StationHour, StationDay, StationYear, StationMonth

logging.basicConfig(level=logging.INFO)
load_dotenv()


class DatabaseHandle:
    def __init__(self):
        pass

    def insertDevices(self, data_devices, db: Session):
        try:
            device = insert(Device).values(
                dev_id=data_devices['dev_id'],
                dev_name=data_devices['dev_name'],
                dev_type_id=data_devices['dev_type_id'],
                esn_code=data_devices['esn_code'],
                station_code=data_devices['station_code'],
                latitude=data_devices['latitude'],
                longitude=data_devices['longitude'],
                software_version=data_devices['software_version'],
            )
            device = device.on_conflict_do_update(
                constraint='dev_id',
                set_=dict(
                    dev_name=data_devices['dev_name'],
                    dev_type_id=data_devices['dev_type_id'],
                    esn_code=data_devices['esn_code'],
                    station_code=data_devices['station_code'],
                    latitude=data_devices['latitude'],
                    longitude=data_devices['longitude'],
                    software_version=data_devices['software_version'],
                )
            )
            db.execute(device)
            db.commit()
            logging.info("Devices inserted or updated successfully!")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error devices insert or update: {e}")

    def insertInv(self, data_inv, db: Session):
        try:
            inv_obj = []
            for item in data_inv:
                inv = Inverter(
                    dev_id=item['dev_id'],
                    mppt_total_cap=item['mppt_total_cap'],
                    pv20_u=item['pv20_u'],
                    pv15_i=item['pv15_i'],
                    close_time=item['close_time'],
                    pv6_i=item['pv6_i'],
                    pv23_u=item['pv23_u'],
                    mppt_10_cap=item['mppt_10_cap'],
                    pv16_i=item['pv16_i'],
                    pv1_i=item['pv1_i'],
                    pv26_i=item['pv26_i'],
                    pv24_i=item['pv24_i'],
                    pv19_u=item['pv19_u'],
                    efficiency=item['efficiency'],
                    pv19_i=item['pv19_i'],
                    pv8_i=item['pv8_i'],
                    inverter_state=item['inverter_state'],
                    pv16_u=item['pv16_u'],
                    pv18_i=item['pv18_i'],
                    pv28_u=item['pv28_u'],
                    pv2_u=item['pv2_u'],
                    pv8_u=item['pv8_u'],
                    pv15_u=item['pv15_u'],
                    pv17_i=item['pv17_i'],
                    mppt_7_cap=item['mppt_7_cap'],
                    mppt_6_cap=item['mppt_6_cap'],
                    pv9_u=item['pv9_u'],
                    pv18_u=item['pv18_u'],
                    day_cap=item['day_cap'],
                    pv3_i=item['pv3_i'],
                    pv28_i=item['pv28_i'],
                    open_time=item['open_time'],
                    a_u=item['a_u'],
                    pv11_i=item['pv11_i'],
                    mppt_5_cap=item['mppt_5_cap'],
                    pv27_i=item['pv27_i'],
                    pv25_u=item['pv25_u'],
                    temperature=item['temperature'],
                    pv12_i=item['pv12_i'],
                    mppt_2_cap=item['mppt_2_cap'],
                    pv4_u=item['pv4_u'],
                    pv22_u=item['pv22_u'],
                    reactive_power=item['reactive_power'],
                    pv13_i=item['pv13_i'],
                    pv27_u=item['pv27_u'],
                    pv1_u=item['pv1_u'],
                    total_cap=item['total_cap'],
                    bc_u=item['bc_u'],
                    pv14_i=item['pv14_i'],
                    pv5_i=item['pv5_i'],
                    pv22_i=item['pv22_i'],
                    a_i=item['a_i'],
                    pv17_u=item['pv17_u'],
                    pv11_u=item['pv11_u'],
                    pv2_i=item['pv2_i'],
                    pv3_u=item['pv3_u'],
                    b_i=item['b_i'],
                    b_u=item['b_u'],
                    pv12_u=item['pv12_u'],
                    ab_u=item['ab_u'],
                    power_factor=item['power_factor'],
                    pv24_u=item['pv24_u'],
                    c_u=item['c_u'],
                    mppt_power=item['mppt_power'],
                    active_power=item['active_power'],
                    pv23_i=item['pv23_i'],
                    mppt_3_cap=item['mppt_3_cap'],
                    pv21_i=item['pv21_i'],
                    mppt_1_cap=item['mppt_1_cap'],
                    ca_u=item['ca_u'],
                    pv6_u=item['pv6_u'],
                    c_i=item['c_i'],
                    mppt_8_cap=item['mppt_8_cap'],
                    pv13_u=item['pv13_u'],
                    pv4_i=item['pv4_i'],
                    pv5_u=item['pv5_u'],
                    pv21_u=item['pv21_u'],
                    elec_freq=item['elec_freq'],
                    pv14_u=item['pv14_u'],
                    pv7_i=item['pv7_i'],
                    mppt_9_cap=item['mppt_9_cap'],
                    pv20_i=item['pv20_i'],
                    run_state=item['run_state'],
                    pv25_i=item['pv25_i'],
                    mppt_4_cap=item['mppt_4_cap'],
                    pv10_u=item['pv10_u'],
                    pv10_i=item['pv10_i'],
                    pv7_u=item['pv7_u'],
                    pv26_u=item['pv26_u'],
                    pv9_i=item['pv9_i'],
                    sn=item['sn'],
                    station_code=item['station_code'],
                )
                inv_obj.append(inv)
            if inv_obj:
                db.add_all(inv_obj)
                db.commit()
                logging.info("Inverter inserted successfully!")
            else:
                logging.info("No new Inverter records to insert.")
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error inv insert: {e}")

    def insertEnergy(self, data_energy, db: Session):
        try:
            energy_obj = []
            for item in data_energy:
                energy = Energy(
                    dev_id=item['dev_id'],
                    positive_reactive_peak=item['positive_reactive_peak'],
                    a_u=item['a_u'],
                    reverse_reactive_power=item['reverse_reactive_power'],
                    positive_active_top=item['positive_active_top'],
                    reverse_reactive_top=item['reverse_reactive_top'],
                    forward_reactive_cap=item['forward_reactive_cap'],
                    active_power=item['active_power'],
                    positive_reactive_valley=item['positive_reactive_valley'],
                    active_cap=item['active_cap'],
                    reverse_reactive_peak=item['reverse_reactive_peak'],
                    reactive_power=item['reactive_power'],
                    positive_reactive_top=item['positive_reactive_top'],
                    reverse_reactive_cap=item['reverse_reactive_cap'],
                    reverse_active_power=item['reverse_active_power'],
                    reactive_power_b=item['reactive_power_b'],
                    ab_u=item['ab_u'],
                    sn=item['sn'],
                    power_factor=item['power_factor'],
                    reverse_active_peak=item['reverse_active_peak'],
                    c_u=item['c_u'],
                    active_power_b=item['active_power_b'],
                    positive_active_power=item['positive_active_power'],
                    reverse_active_top=item['reverse_active_top'],
                    reactive_power_c=item['reactive_power_c'],
                    ca_u=item['ca_u'],
                    station_code=item['station_code'],
                    a_i=item['a_i'],
                    positive_active_peak=item['positive_active_peak'],
                    total_apparent_power=item['total_apparent_power'],
                    active_power_a=item['active_power_a'],
                    positive_active_valley=item['positive_active_valley'],
                    reactive_power_a=item['reactive_power_a'],
                    reverse_active_valley=item['reverse_active_valley'],
                    positive_reactive_power=item['positive_reactive_power'],
                    c_i=item['c_i'],
                    bc_u=item['bc_u'],
                    active_power_c=item['active_power_c'],
                    b_i=item['b_i'],
                    b_u=item['b_u'],
                    grid_frequency=item['grid_frequency'],
                    reverse_reactive_valley=item['reverse_reactive_valley'],
                    reverse_active_cap=item['reverse_active_cap'],
                )
                energy_obj.append(energy)
            if energy_obj:
                db.add_all(energy_obj)
                db.commit()
                logging.info("Energy inserted successfully!")
            else:
                logging.info("No new Energy records to insert.")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error energy insert: {e}")

    def insertSensorEnergy(self, data_sensor_energy, db: Session):
        try:
            inv_energy_obj = []
            for item in data_sensor_energy:
                inv_energy = SensorEnergy(
                    dev_id=item['dev_id'],
                    meter_status=item['meter_status'],
                    active_cap=item['active_cap'],
                    meter_i=item['meter_i'],
                    power_factor=item['power_factor'],
                    c_i=item['c_i'],
                    meter_u=item['meter_u'],
                    b_i=item['b_i'],
                    reverse_reactive_valley=item['reverse_reactive_valley'],
                    positive_reactive_peak=item['positive_reactive_peak'],
                    reverse_reactive_peak=item['reverse_reactive_peak'],
                    reverse_active_peak=item['reverse_active_peak'],
                    positive_active_peak=item['positive_active_peak'],
                    reactive_power=item['reactive_power'],
                    c_u=item['c_u'],
                    total_apparent_power=item['total_apparent_power'],
                    bc_u=item['bc_u'],
                    b_u=item['b_u'],
                    reverse_active_cap=item['reverse_active_cap'],
                    reverse_reactive_power=item['reverse_reactive_power'],
                    positive_reactive_top=item['positive_reactive_top'],
                    active_power_b=item['active_power_b'],
                    active_power_a=item['active_power_a'],
                    positive_active_top=item['positive_active_top'],
                    reverse_reactive_cap=item['reverse_reactive_cap'],
                    positive_active_power=item['positive_active_power'],
                    positive_active_valley=item['positive_active_valley'],
                    run_state=item['run_state'],
                    reverse_reactive_top=item['reverse_reactive_top'],
                    reverse_active_power=item['reverse_active_power'],
                    reverse_active_top=item['reverse_active_top'],
                    reactive_power_a=item['reactive_power_a'],
                    forward_reactive_cap=item['forward_reactive_cap'],
                    reactive_power_b=item['reactive_power_b'],
                    reactive_power_c=item['reactive_power_c'],
                    reverse_active_valley=item['reverse_active_valley'],
                    active_power=item['active_power'],
                    ab_u=item['ab_u'],
                    ca_u=item['ca_u'],
                    positive_reactive_power=item['positive_reactive_power'],
                    active_power_c=item['active_power_c'],
                    grid_frequency=item['grid_frequency'],
                    positive_reactive_valley=item['positive_reactive_valley'],
                    sn=item['sn'],
                    station_code=item['station_code'],
                )
                inv_energy_obj.append(inv_energy)
            if inv_energy_obj:
                db.add_all(inv_energy_obj)  # Corrected line
                db.commit()
                logging.info("Sensor energy inserted successfully!")
            else:
                logging.info("No new Sensor energy records to insert.")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error sensor energy insert: {e}")

    def insertStation(self, data_station, db: Session):
        try:
            station_obj = []
            for item in data_station:
                station_exists = db.query(Station).filter(
                    Station.station_code == item['station_code']).first()
                if not station_exists:
                    stations = insert(Station).values(
                        stations=data_station['stations'],
                        total_income=data_station['total_income'],
                        total_power=data_station['total_power'],
                        day_power=data_station['day_power'],
                        day_income=data_station['day_income'],
                        real_health_state=data_station['real_health_state'],
                        month_power=data_station['month_power'],
                        station_code=data_station['station_code'],
                    )
                    station_obj.append(stations)

            if station_obj:
                db.add_all(station_obj)
                db.commit()
                logging.info(
                    f"Inserted {len(station_obj)} Station records successfully!")
            else:
                logging.info("No new Station records to insert.")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error station insert or update: {e}")

    def insertStationHour(self, data_stationhour, db: Session):
        try:
            stationhour_obj = []
            for item in data_stationhour:
                stationhour_exists = db.query(StationHour).filter(
                    StationHour.collect_time == item['collect_time'],
                    StationHour.station_code == item['station_code']
                ).first()

                if not stationhour_exists:
                    stationhour = StationHour(
                        collect_time=item['collect_time'],
                        radiation_intensity=item['radiation_intensity'],
                        theory_power=item['theory_power'],
                        inverter_power=item['inverter_power'],
                        ongrid_power=item['ongrid_power'],
                        power_profit=item['power_profit'],
                        station_code=item['station_code']
                    )
                    stationhour_obj.append(stationhour)

            if stationhour_obj:
                db.add_all(stationhour_obj)
                db.commit()
                logging.info(
                    f"Inserted {len(stationhour_obj)} StationHour records successfully!")
            else:
                logging.info("No new StationHour records to insert.")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error inserting or updating station hour: {e}")

    def insertStationDay(self, data_stationday, db: Session):
        try:

            stationday_obj = []
            for item in data_stationday:
                stationday_exists = db.query(StationDay).filter(
                    StationDay.collect_time == item['collect_time'],
                    StationDay.station_code == item['station_code']
                ).first()
                if not stationday_exists:
                    stationday = StationDay(
                        collect_time=item['collect_time'],
                        inverter_power=item['inverter_power'],
                        self_use_power=item['self_use_power'],
                        power_profit=item['power_profit'],
                        perpower_ratio=item['perpower_ratio'],
                        reduction_total_co2=item['reduction_total_co2'],
                        self_provide=item['self_provide'],
                        installed_capacity=item['installed_capacity'],
                        use_power=item['use_power'],
                        reduction_total_coal=item['reduction_total_coal'],
                        ongrid_power=item['ongrid_power'],
                        buy_power=item['buy_power'],
                        station_code=item['station_code']
                    )
                    stationday_obj.append(stationday)
            if stationday_obj:
                db.add_all(stationday_obj)
                db.commit()
                logging.info("Station inserted day successfully!")
            else:
                logging.info("Station day already exists, not inserting.")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error inserting or updating station day: {e}")

    def insertStationMonth(self, data_stationmonth, db: Session):
        try:
            stationmonth_obj = []
            for item in data_stationmonth:
                stationmonth_exists = db.query(StationMonth).filter(
                    StationMonth.collect_time == item['collect_time'],
                    StationMonth.station_code == item['station_code'],
                ).first()
                if not stationmonth_exists:
                    stationmonth = StationMonth(
                        collect_time=item['collect_time'],
                        inverter_power=item['inverter_power'],
                        self_use_power=item['self_use_power'],
                        power_profit=item['power_profit'],
                        perpower_ratio=item['perpower_ratio'],
                        reduction_total_co2=item['reduction_total_co2'],
                        self_provide=item['self_provide'],
                        installed_capacity=item['installed_capacity'],
                        use_power=item['use_power'],
                        reduction_total_coal=item['reduction_total_coal'],
                        ongrid_power=item['ongrid_power'],
                        buy_power=item['buy_power'],
                        station_code=item['station_code'],
                    )
                    stationmonth_obj.append(stationmonth)

            if stationmonth_obj:
                db.add_all(stationmonth_obj)
                db.commit()
                logging.info("Station inserted month or updated successfully!")
            else:
                logging.info("No new records to insert.")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error inserting or updating station month: {e}")

    def insertStationYear(self, data_stationyear, db: Session):
        try:
            stationyear_obj = []
            for item in data_stationyear:
                stationyear_exists = db.query(StationYear).filter(
                    StationYear.collect_time == item['collect_time'],
                    StationYear.station_code == item['station_code']
                ).first()
                if not stationyear_exists:
                    stationyear = StationYear(
                        collect_time=item['collect_time'],
                        inverter_power=item['inverter_power'],
                        self_use_power=item['self_use_power'],
                        reduction_total_tree=item['reduction_total_tree'],
                        power_profit=item['power_profit'],
                        perpower_ratio=item['perpower_ratio'],
                        reduction_total_co2=item['reduction_total_co2'],
                        self_provide=item['self_provide'],
                        installed_capacity=item['installed_capacity'],
                        use_power=item['use_power'],
                        reduction_total_coal=item['reduction_total_coal'],
                        ongrid_power=item['ongrid_power'],
                        buy_power=item['buy_power'],
                        station_code=item['station_code']
                    )
                    stationyear_obj.append(stationyear)

            if stationyear_obj:
                db.add_all(stationyear_obj)
                db.commit()
                logging.info("Station inserted year or updated successfully!")
            else:
                logging.info("No new records to insert for StationYear.")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error inserting or updating station year: {e}")

    def insertMsStation(self, data_ms_station, db: Session):
        try:
            ms_station = insert(MsStations).values(
                station_code=data_ms_station['station_code'],
                capacity=data_ms_station['capacity'],
                grid_connection_date=data_ms_station['grid_connection_date'],
                latitude=data_ms_station['latitude'],
                longitude=data_ms_station['longitude'],
                station_address=data_ms_station['station_address'],
                station_name=data_ms_station['station_name'],
            )
            ms_station = ms_station.on_conflict_do_update(
                constraint='station_code',
                set_=dict(
                    capacity=data_ms_station['capacity'],
                    grid_connection_date=data_ms_station['grid_connection_date'],
                    latitude=data_ms_station['latitude'],
                    longitude=data_ms_station['longitude'],
                    station_address=data_ms_station['station_address'],
                    station_name=data_ms_station['station_name'],
                )
            )
            db.execute(ms_station)
            db.commit()
            logging.info("MS_station inserted or updated successfully!")

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Error ms_station insert or update: {e}")


