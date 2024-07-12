from sqlalchemy import Column, Integer, Float, String,BigInteger,Boolean ,Time,TIMESTAMP, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base,engine

# Define your SQLAlchemy models
class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    value_name = Column(String, nullable=False)
    value = Column(String)
    data_type = Column(String)
    expression = Column(String)
    description = Column(String)
    group_name = Column(String)
    timestamp = Column(DateTime, nullable=True)
    data_type_code = Column(Integer, nullable=False)

class DeviceType(Base):
    __tablename__ = 'device_types'

    id = Column(Integer, primary_key=True)
    dev_type_id = Column(Integer, unique=True)
    dev_type_name = Column(String)


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    tariff_type = Column(Integer, ForeignKey("tariff.id"))
    esn_code = Column(String)
    dev_id = Column(BigInteger, nullable=False, unique=True)
    dev_type_id = Column(Integer, ForeignKey('device_types.dev_type_id'))
    dev_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    software_version = Column(String)
    installation_date = Column(DateTime) 
    exd_warranty = Column(DateTime) 
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())


class Tariff(Base):
    __tablename__ = 'tariff'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tod_rate_min = Column(Float)
    tod_rate_mid = Column(Float)
    tod_rate_max = Column(Float)
    tou_on_pk_rate_min = Column(Float)
    tou_on_pk_rate_mid = Column(Float)
    tou_on_pk_rate_max = Column(Float)
    tou_off_pk_rate_min = Column(Float)
    tou_off_pk_rate_mid = Column(Float)
    tou_off_pk_rate_max = Column(Float)
    tou_on_pk_time_from = Column(Time)
    tou_on_pk_time_to = Column(Time)
    tou_off_pk_time_from = Column(Time)
    tou_off_pk_time_to = Column(Time)
    ft = Column(Float)
    dsc = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
    volt_rate_min = Column(String)
    volt_rate_mid = Column(String)
    volt_rate_max = Column(String)


class Energy(Base):
    __tablename__ = 'energy'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now())
    dev_id = Column(BigInteger)
    active_cap = Column(Float)
    power_factor = Column(Float)
    a_i = Column(Float)
    c_i = Column(Float)
    b_i = Column(Float)
    reverse_reactive_valley = Column(Float)
    positive_reactive_peak = Column(Float)
    reverse_reactive_peak = Column(Float)
    reverse_active_peak = Column(Float)
    positive_active_peak = Column(Float)
    a_u = Column(Float)
    reactive_power = Column(Float)
    c_u = Column(Float)
    total_apparent_power = Column(Float)
    bc_u = Column(Float)
    b_u = Column(Float)
    reverse_active_cap = Column(Float)
    reverse_reactive_power = Column(Float)
    positive_reactive_top = Column(Float)
    active_power_b = Column(Float)
    active_power_a = Column(Float)
    positive_active_top = Column(Float)
    reverse_reactive_cap = Column(Float)
    positive_active_power = Column(Float)
    positive_active_valley = Column(Float)
    reverse_reactive_top = Column(Float)
    reverse_active_power = Column(Float)
    reverse_active_top = Column(Float)
    reactive_power_a = Column(Float)
    forward_reactive_cap = Column(Float)
    reactive_power_b = Column(Float)
    reactive_power_c = Column(Float)
    reverse_active_valley = Column(Float)
    active_power = Column(Float)
    ab_u = Column(Float)
    ca_u = Column(Float)
    positive_reactive_power = Column(Float)
    active_power_c = Column(Float)
    grid_frequency = Column(Float)
    positive_reactive_valley = Column(Float)
    sn = Column(String)
    station_code = Column(Integer)
    __table_args__ = (
        UniqueConstraint('dev_id', 'sn', name='energy_dev_id_sn_unique'),
    )

class SensorEnergy(Base):
    __tablename__ = 'sensor_energy'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now())
    dev_id = Column(BigInteger)
    meter_status = Column(Integer)
    active_cap = Column(Float)
    meter_i = Column(Float)
    power_factor = Column(Float)
    c_i = Column(Float)
    meter_u = Column(Float)
    b_i = Column(Float)
    reverse_reactive_valley = Column(Float)
    positive_reactive_peak = Column(Float)
    reverse_reactive_peak = Column(Float)
    reverse_active_peak = Column(Float)
    positive_active_peak = Column(Float)
    reactive_power = Column(Float)
    c_u = Column(Float)
    total_apparent_power = Column(Float)
    bc_u = Column(Float)
    b_u = Column(Float)
    reverse_active_cap = Column(Float)
    reverse_reactive_power = Column(Float)
    positive_reactive_top = Column(Float)
    active_power_b = Column(Float)
    active_power_a = Column(Float)
    positive_active_top = Column(Float)
    reverse_reactive_cap = Column(Float)
    positive_active_power = Column(Float)
    positive_active_valley = Column(Float)
    run_state = Column(Integer)
    reverse_reactive_top = Column(Float)
    reverse_active_power = Column(Float)
    reverse_active_top = Column(Float)
    reactive_power_a = Column(Float)
    forward_reactive_cap = Column(Float)
    reactive_power_b = Column(Float)
    reactive_power_c = Column(Float)
    reverse_active_valley = Column(Float)
    active_power = Column(Float)
    ab_u = Column(Float)
    ca_u = Column(Float)
    positive_reactive_power = Column(Float)
    active_power_c = Column(Float)
    grid_frequency = Column(Float)
    positive_reactive_valley = Column(Float)
    sn = Column(String)
    station_code = Column(Integer)
    
class Inverter(Base):
    __tablename__ = 'inverter'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now())
    dev_id = Column(BigInteger)
    pv26_i	=	Column(Float)
    pv2_u	=	Column(Float)
    pv28_i	=	Column(Float)
    pv4_u	=	Column(Float)
    pv22_i	=	Column(Float)
    power_factor	=	Column(Float)
    pv6_u	=	Column(Float)
    mppt_total_cap	=	Column(Float)
    pv24_i	=	Column(Float)
    pv8_u	=	Column(Float)
    open_time	=	Column(BigInteger)
    pv22_u	=	Column(Float)
    a_i	=	Column(Float)
    pv24_u	=	Column(Float)
    c_i	=	Column(Float)
    mppt_9_cap	=	Column(Float)
    pv20_u	=	Column(Float)
    pv19_u	=	Column(Float)
    pv15_u	=	Column(Float)
    a_u	=	Column(Float)
    reactive_power	=	Column(Float)
    pv17_u	=	Column(Float)
    c_u	=	Column(Float)
    mppt_8_cap	=	Column(Float)
    pv20_i	=	Column(Float)
    pv15_i	=	Column(Float)
    efficiency	=	Column(Float)
    pv17_i	=	Column(Float)
    pv11_i	=	Column(Float)
    pv13_i	=	Column(Float)
    pv11_u	=	Column(Float)
    mppt_power	=	Column(Float)
    pv13_u	=	Column(Float)
    run_state	=	Column(Float)
    close_time	=	Column(BigInteger)
    pv19_i	=	Column(Float)
    mppt_7_cap	=	Column(Float)
    mppt_5_cap	=	Column(Float)
    pv27_u	=	Column(Float)
    pv2_i	=	Column(Float)
    active_power	=	Column(Float)
    pv4_i	=	Column(Float)
    pv6_i	=	Column(Float)
    pv8_i	=	Column(Float)
    mppt_6_cap	=	Column(Float)
    pv27_i	=	Column(Float)
    pv1_u	=	Column(Float)
    pv3_u	=	Column(Float)
    pv23_i	=	Column(Float)
    pv5_u	=	Column(Float)
    pv25_i	=	Column(Float)
    pv7_u	=	Column(Float)
    pv23_u	=	Column(Float)
    inverter_state	=	Column(Integer)
    pv9_u	=	Column(Float)
    pv25_u	=	Column(Float)
    total_cap	=	Column(Float)
    b_i	=	Column(Float)
    mppt_3_cap	=	Column(Float)
    pv21_u	=	Column(Float)
    mppt_10_cap	=	Column(Float)
    pv16_u	=	Column(Float)
    pv18_u	=	Column(Float)
    temperature	=	Column(Float)
    bc_u	=	Column(Float)
    b_u	=	Column(Float)
    pv21_i	=	Column(Float)
    elec_freq	=	Column(Float)
    mppt_4_cap	=	Column(Float)
    pv16_i	=	Column(Float)
    pv18_i	=	Column(Float)
    day_cap	=	Column(Float)
    pv12_i	=	Column(Float)
    pv14_i	=	Column(Float)
    pv12_u	=	Column(Float)
    mppt_1_cap	=	Column(Float)
    pv14_u	=	Column(Float)
    pv10_u	=	Column(Float)
    pv26_u	=	Column(Float)
    pv1_i	=	Column(Float)
    pv28_u	=	Column(Float)
    pv3_i	=	Column(Float)
    mppt_2_cap	=	Column(Float)
    pv5_i	=	Column(Float)
    ab_u	=	Column(Float)
    ca_u	=	Column(Float)
    pv7_i	=	Column(Float)
    pv10_i	=	Column(Float)
    pv9_i	=	Column(Float)
    sn	=	Column(String)
    station_code	=	Column(Integer)

class MsInverters(Base):
    __tablename__ = 'ms_inverters'

    id = Column(Integer, primary_key=True)
    esn_code = Column(String)
    inverter_state = Column(Integer)
    inv_type = Column(String)
    last_active_power = Column(Float)
    last_update = Column(Float)
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())

class MsStations(Base):
    __tablename__ = 'ms_stations'

    id = Column(Integer, primary_key=True)
    capacity = Column(Float)
    grid_connection_date = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    station_address = Column(String)
    station_code = Column(Integer, unique=True, nullable=False)
    station_name = Column(String)
    timestamp = Column(DateTime, default=datetime.now())

class Station(Base):
    __tablename__ = 'stations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_income = Column(Float)
    total_power = Column(Float)
    day_power = Column(Float)
    day_income = Column(Float)
    real_health_state = Column(Float)
    month_power = Column(Float)
    station_code = Column(Integer, unique=True)
    station_name = Column(String)
    station_address = Column(String)
    timestamp = Column(DateTime, default=datetime.now())


class StationHour(Base):
    __tablename__ = 'stations_hour'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    collect_time = Column(BigInteger)
    radiation_intensity = Column(Float)
    theory_power = Column(Float)
    inverter_power = Column(Float)
    ongrid_power = Column(Float)
    power_profit = Column(Float)
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())

class StationDay(Base):
    __tablename__ = 'stations_day'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    collect_time = Column(BigInteger)
    inverter_power = Column(Float)
    self_use_power = Column(Float)
    power_profit = Column(Float)
    perpower_ratio = Column(Float)
    reduction_total_co2 = Column(Float)
    self_provide = Column(Float)
    installed_capacity = Column(Float)
    use_power = Column(Float)
    reduction_total_coal = Column(Float)
    ongrid_power = Column(Float)
    buy_power = Column(Float)
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())

class StationMonth(Base):
    __tablename__ = 'stations_month'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    collect_time = Column(BigInteger)
    inverter_power = Column(Float)
    self_use_power = Column(Float)
    power_profit = Column(Float)
    perpower_ratio = Column(Float)
    reduction_total_co2 = Column(Float)
    self_provide = Column(Float)
    installed_capacity = Column(Float)
    use_power = Column(Float)
    reduction_total_coal = Column(Float)
    ongrid_power = Column(Float)
    buy_power = Column(Float)
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())

class StationYear(Base):
    __tablename__ = 'stations_year'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    collect_time = Column(BigInteger)
    inverter_power = Column(Float)
    self_use_power = Column(Float)
    reduction_total_tree = Column(Float)
    power_profit = Column(Float)
    perpower_ratio = Column(Float)
    reduction_total_co2 = Column(Float)
    self_provide = Column(Float)
    installed_capacity = Column(Float)
    use_power = Column(Float)
    reduction_total_coal = Column(Float)
    ongrid_power = Column(Float)
    buy_power = Column(Float)
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())
    
class Tou(Base):
    __tablename__ = 'tou'

    id = Column(Integer, primary_key=True)
    on_date = Column(DateTime)
    yield_off_peak = Column(Float)
    yield_on_peak = Column(Float)
    yield_total = Column(Float)
    revenue = Column(Float)
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())

class Tod(Base):
    __tablename__ = 'tod'

    id = Column(Integer, primary_key=True)
    on_date = Column(DateTime)
    yield_total = Column(Float)
    revenue = Column(Float)
    station_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now())


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    avatar = Column(String)
    creation_date = Column(DateTime)
    last_access_date = Column(DateTime)
    updated_at = Column(DateTime)
    enabled = Column(Boolean)
    line_token = Column(String)
    line_code = Column(String)

class Environment(Base):
    __tablename__ = "environment"

    id = Column(Integer, primary_key=True)
    station_code = Column(Integer, ForeignKey("ms_stations.station_code"), nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    rh = Column(Float, nullable=True) 
    tc = Column(Float, nullable=True)  
    rain = Column(Float, nullable=True)
    cond_th = Column(String, nullable=True) 
    cond_en = Column(String, nullable=True)  
    irr = Column(Float, nullable=True) 
    wind_speed = Column(Float, nullable=True)
    wind_direc = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint('station_code', name='environment_station_code_unique'),
    )

Base.metadata.create_all(engine)
