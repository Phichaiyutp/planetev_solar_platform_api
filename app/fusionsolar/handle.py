import os
from types import NoneType
import requests
import json
import time
import datetime
import schedule
import urllib3
from jsonpointer import resolve_pointer
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.fusionsolar.db import DatabaseHandle

load_dotenv()
logging.basicConfig(level=logging.INFO)

urllib3.disable_warnings()

db_handle = DatabaseHandle()

class ApiHandle():
    def __init__(self):
        self.xsrf_token = None
        self.plantCode: str = None
        self.esnCode: str = None
        self.devicesList: dict[str, str] = None
        self.time_travel = 0

    def DevList(self,db: Session):
        
        urlGetMsStation = 'https://sg5.fusionsolar.huawei.com/thirdData/getDevList'
        if not self.xsrf_token:
            self.xsrf_token = self.getSolarApiToken()
        plantCode = self.listPlantCode()
        payload = {
            "stationCodes": plantCode
        }
        dataStations = json.loads(self.requestsSolarAPI(payload, urlGetMsStation))
        if dataStations['success']:
            with open(os.path.join(os.path.dirname(__file__), 'config', 'dataStations.json'), 'w') as f:
                if len(dataStations) > 0:
                    json.dump(dataStations, f)
            data_values = [(dev['devName'], dev['devTypeId'], dev['esnCode'], dev['id'], dev['latitude'], dev['longitude'],
                            dev['softwareVersion'], dev['stationCode'][3:]) for dev in dataStations['data']]
        db_handle.insertDevices(data_values,db)
        return dataStations

    def KpiMsStation(self,db: Session):
        
        urlGetMsStation = 'https://sg5.fusionsolar.huawei.com/thirdData/stations'
        if not self.xsrf_token:
            self.xsrf_token = self.getSolarApiToken()
        payload = {
            "pageNo": 1
        }
        dataMsStation = self.requestsSolarAPI(payload, urlGetMsStation)
        if dataMsStation:
            global plantCode
            data = json.loads(dataMsStation)
            plantCode_arr = [plant['plantCode'] for plant in data['data']['list']]
            plantCode = ','.join(plantCode_arr)
            with open(os.path.join(os.path.dirname(__file__), 'config', 'dataMsStation.json'), 'w', encoding='utf-8') as f:
                f.write(dataMsStation)
            db_handle.insertMsStation(self.convertMsStationData(dataMsStation),db)

    def StationsConf(self):
        with open(os.path.join(os.path.dirname(__file__), 'config', 'dataMsStation.json'), 'r', encoding='utf-8') as file:
            data1 = json.load(file)

        # Load the second JSON file
        with open(os.path.join(os.path.dirname(__file__), 'config', 'dataStations.json'), 'r', encoding='utf-8') as file:
            data2 = json.load(file)

        # Extract data from both JSON files
        list1 = data1['data']['list']
        list2 = data2['data']

        # Create a dictionary to map station codes to their respective data
        station_map = {item['stationCode']: item for item in list2}

        # Merge the data based on the station code
        merged_data = []
        for item in list1:
            station_code = item['plantCode']
            if station_code in station_map:
                station_data = station_map[station_code]
                merged_item = {
                    "plantCode": station_code,
                    "plantName": item["plantName"],
                    "plantAddress": item["plantAddress"],
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "stationCode": station_data["stationCode"],
                    "devName": station_data["devName"],
                    "devTypeId": station_data["devTypeId"],
                    "esnCode": station_data["esnCode"],
                    "id": station_data["id"],
                    "invType": station_data["invType"],
                    "softwareVersion": station_data["softwareVersion"]
                }
                merged_data.append(merged_item)
        with open(os.path.join(os.path.dirname(__file__), 'config', 'StationsConf.json'), 'w', encoding='utf-8') as file:
            json.dump(merged_data, file, ensure_ascii=False, indent=2)
        return merged_data

    def EsnCode(self):
        with open(os.path.join(os.path.dirname(__file__), 'config', 'dataStations.json'), 'r', encoding='utf-8') as file:
            parsed_data = json.load(file)
        esn2station = {}
        for item in parsed_data['data']:
            esn_code = item['esnCode']
            id = item['id']
            station_code = item['stationCode'].split('=')[1]
            key = esn_code if esn_code else id
            esn2station[key] = {"plantCode": int(station_code)}

        with open(os.path.join(os.path.dirname(__file__), 'config', 'esn2station.json'), 'w') as f:
            json.dump(esn2station, f)
        return esn2station

    def  DevRealKpi(self,db: Session):
        try:
            urlGetDevice = 'https://sg5.fusionsolar.huawei.com/thirdData/getDevRealKpi'
            if not self.xsrf_token:
                self.xsrf_token = self.getSolarApiToken()
            devicesList = self.listDevices()
            payloadInv = {
                "devIds": devicesList["inv"],
                "devTypeId": 1
            }
            dataInv = self.requestsSolarAPI(payloadInv, urlGetDevice)
            if dataInv:
                #print(self.convertDevData(dataInv, 1))
                db_handle.insertInv(self.convertDevData(dataInv, 1),db)
            payloadEnergy = {
                "devIds": devicesList["energy"],
                "devTypeId": 17
            }
            dataEnergy = self.requestsSolarAPI(payloadEnergy, urlGetDevice)
            if dataEnergy:
                #print(self.convertDevData(dataEnergy, 17))
                db_handle.insertEnergy(self.convertDevData(dataEnergy, 17),db)
            payloadSensorEnergy = {
                "devIds": devicesList["sensor_energy"],
                "devTypeId": 47
            }
            dataSensorEnergy = self.requestsSolarAPI(payloadSensorEnergy, urlGetDevice)
            if dataSensorEnergy:
                #print(self.convertDevData(dataSensorEnergy, 47))
                db_handle.insertSensorEnergy(self.convertDevData(dataSensorEnergy, 47),db)
        except Exception as e:
            logging.error(f"Error DevRealKpi: {e}")
        
    def KpiStationHour(self,db: Session):
        try:
            urlGetStationDay = 'https://sg5.fusionsolar.huawei.com/thirdData/getKpiStationHour'
            if not self.xsrf_token:
                self.xsrf_token = self.getSolarApiToken()
            plantCode = self.listPlantCode()
            local_time = datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=(self.time_travel))
            unix_timestamp = local_time.timestamp()
            millisec = int(unix_timestamp * 1000)
            payload = {
                "stationCodes": plantCode,
                "collectTime": millisec
            }

            dataStationHour = self.requestsSolarAPI(payload, urlGetStationDay)
            if dataStationHour:
                db_handle.insertStationHour(self.convertStationSumData(dataStationHour, 'hour'),db)
                return {'ok':True}
            
        except Exception as e:
            logging.error(f"KpiStationHour Error: {e}")
            return {'ok':False}

    def KpiStationDay(self,db: Session):
        try:
            urlGetStationDay = 'https://sg5.fusionsolar.huawei.com/thirdData/getKpiStationDay'
            if not self.xsrf_token:
                self.xsrf_token = self.getSolarApiToken()
            plantCode = self.listPlantCode()
            local_time = datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=(self.time_travel))
            unix_timestamp = local_time.timestamp()
            millisec = int(unix_timestamp * 1000)
            payload = {
                "stationCodes": plantCode,
                "collectTime": millisec
            }
            dataStationDay = self.requestsSolarAPI(payload, urlGetStationDay)
            if dataStationDay:
                db_handle.insertStationDay(self.convertStationSumData(dataStationDay, 'day'),db)
                return  {'ok':True}
            
        except Exception as e:
            logging.error(f"KpiStationDay Error: {e}")
            return {'ok':False}
        
    def KpiStationMonth(self,db: Session):
        try :
            urlGetStationMonth = 'https://sg5.fusionsolar.huawei.com/thirdData/getKpiStationMonth'
            if not self.xsrf_token:
                self.xsrf_token = self.getSolarApiToken()
            plantCode = self.listPlantCode()
            local_time = datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0)
            unix_timestamp = local_time.timestamp()
            millisec = int(unix_timestamp * 1000)
            payload = {
                "stationCodes": plantCode,
                "collectTime": millisec
            }
            dataStationMonth = self.requestsSolarAPI(payload, urlGetStationMonth)
            if dataStationMonth:
                db_handle.insertStationMonth(self.convertStationSumData(dataStationMonth, 'month'),db)
                return {'ok':True}
            
        except Exception as e:
            logging.error(f"KpiStationMonth Error: {e}")
            return {'ok':False}
        
    def KpiStationYear(self,db: Session):
        try:
            urlGetStationYear = 'https://sg5.fusionsolar.huawei.com/thirdData/getKpiStationYear'
            if not self.xsrf_token:
                self.xsrf_token = self.getSolarApiToken()
            plantCode = self.listPlantCode()
            local_time = datetime.datetime.now().replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            unix_timestamp = local_time.timestamp()
            millisec = int(unix_timestamp * 1000)
            payload = {
                "stationCodes": plantCode,
                "collectTime": millisec
            }
            dataStationYear = self.requestsSolarAPI(payload, urlGetStationYear)
            if dataStationYear:
                db_handle.insertStationYear(self.convertStationSumData(dataStationYear, 'year'),db)
                return {'ok':True}
            
        except Exception as e:
            logging.error(f"KpiStationYear Error: {e}")
            return {'ok':False}
        
    def getSolarApiToken(self):
        
        try:
            url_login = 'https://sg5.fusionsolar.huawei.com/thirdData/login'
            api_login = requests.post(url_login, verify=False, json={"userName": os.getenv(
                'FUSIONSOLAR_USER'), "systemCode": os.getenv('FUSIONSOLAR_PASS')})
            headers = api_login.headers
            return headers.get("xsrf-token")
        except Exception as e:
            logging.error(f"Requests API Token Error: {e}")

    def requestsSolarAPI(self,payload: object, endpoin: str):
        try:
            if self.xsrf_token:
                headers = {
                    "XSRF-TOKEN": self.xsrf_token
                }
                r = requests.post(url=endpoin, verify=False,json=payload, headers=headers)
                data = json.loads(r.text)
                if data:
                    match data["failCode"]:
                        case 0:
                            IsSuccess = data["success"]
                            if IsSuccess:
                                return r.text
                            else:
                                return None
                        case 305:
                            self.xsrf_token = self.getSolarApiToken()
                            raise Exception(
                                "You are not in the login state. You need to log in again.")
                        case 407:
                            raise Exception(
                                "The interface access frequency is too high.")
                else:
                    raise Exception("API Not response")
        except Exception as e:
            logging.error(f"Requests API Error: {e}")

    def listPlantCode(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'config', 'dataMsStation.json'), 'r', encoding='utf-8') as file:
                dataMsStation = json.load(file)
            plantCodeArr = [value["plantCode"]
                            for value in dataMsStation["data"]["list"]]
            plantCode = ','.join(plantCodeArr)
            with open(os.path.join(os.path.dirname(__file__), 'config', 'plantCode.json'), 'w') as file:
                json.dump(plantCodeArr, file)
            return plantCode
        except Exception as e:
                logging.error(f"List Plant Code Error: {e}")

    def listDevices(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'config', 'dataStations.json'), 'r', encoding='utf-8') as file:
                data = json.load(file)
            devicesList = {}
            id_inv = []
            id_energy = []
            id_sensor_energy = []
            for index, element in enumerate(data["data"]):
                value_id = element["id"]
                value_type = element["devTypeId"]
                match value_type:
                    case 1:
                        id_inv.append(value_id)
                    case 17:
                        id_energy.append(value_id)
                    case 47:
                        id_sensor_energy.append(value_id)
            devicesList = {"inv": ','.join(map(str, id_inv)), "energy": ','.join(
                map(str, id_energy)), "sensor_energy": ','.join(map(str, id_sensor_energy))}
            return devicesList
        except Exception as e:
            logging.error(f"List Devices Error: {e}")

    def convertMsStationData(self,data: str):
        json_data = json.loads(data)
        data_arr = []
        for payload in json_data["data"]["list"]:
            data_arr.append((
                payload["capacity"],
                payload["gridConnectionDate"],
                payload["latitude"],
                payload["longitude"],
                payload["plantAddress"],
                int(payload["plantCode"].split('=')[1]),
                payload["plantName"]
            ))
        return data_arr

    def convertDevData(self,data: str, devTypeId: int):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'config', 'esn2station.json'), 'r', encoding='utf-8') as file:
                esn2station = json.load(file)
            json_data = json.loads(data)
            data_arr = []
            pointer_list = "/data"
            data_list = resolve_pointer(json_data, pointer_list)
            for index, element in enumerate(data_list):
                pointer = f"/data/{index}"
                data_item = resolve_pointer(json_data, pointer)
                payload = {
                    "devId": data_item["devId"] if data_item["devId"] else 'null',
                    **data_item["dataItemMap"],
                    "sn": data_item["sn"] if data_item["sn"] else 'null',
                }
                if data_item["dataItemMap"]:
                    match devTypeId:
                        case 1:
                            for key in ["pv26_i", "pv2_u", "pv28_i", "pv4_u", "pv22_i", "power_factor", "pv6_u", "mppt_total_cap", "pv24_i", "pv8_u", "open_time", "pv22_u", "a_i", "pv24_u", "c_i", "mppt_9_cap", "pv20_u", "pv19_u", "pv15_u", "a_u", "reactive_power", "pv17_u", "c_u", "mppt_8_cap", "pv20_i", "pv15_i", "efficiency", "pv17_i", "pv11_i", "pv13_i", "pv11_u", "mppt_power", "pv13_u", "run_state", "close_time", "pv19_i", "mppt_7_cap", "mppt_5_cap", "pv27_u", "pv2_i", "active_power", "pv4_i", "pv6_i", "pv8_i", "mppt_6_cap", "pv27_i", "pv1_u", "pv3_u", "pv23_i", "pv5_u", "pv25_i", "pv7_u", "pv23_u", "inverter_state", "pv9_u", "pv25_u", "total_cap", "b_i", "mppt_3_cap", "pv21_u", "mppt_10_cap", "pv16_u", "pv18_u", "temperature", "bc_u", "b_u", "pv21_i", "elec_freq", "mppt_4_cap", "pv16_i", "pv18_i", "day_cap", "pv12_i", "pv14_i", "pv12_u", "mppt_1_cap", "pv14_u", "pv10_u", "pv26_u", "pv1_i", "pv28_u", "pv3_i", "mppt_2_cap", "pv5_i", "ab_u", "ca_u", "pv7_i", "pv10_i", "pv9_i"]:
                                if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                                    payload[key] = 0
                            data_arr.append({
                                "dev_id":payload["devId"],
                                "pv26_i":payload["pv26_i"],
                                "pv2_u":payload["pv2_u"],
                                "pv28_i":payload["pv28_i"],
                                "pv4_u":payload["pv4_u"],
                                "pv22_i":payload["pv22_i"],
                                "power_factor":payload["power_factor"],
                                "pv6_u":payload["pv6_u"],
                                "mppt_total_cap":payload["mppt_total_cap"],
                                "pv24_i":payload["pv24_i"],
                                "pv8_u":payload["pv8_u"],
                                "open_time":payload["open_time"],
                                "pv22_u":payload["pv22_u"],
                                "a_i":payload["a_i"],
                                "pv24_u":payload["pv24_u"],
                                "c_i":payload["c_i"],
                                "mppt_9_cap":payload["mppt_9_cap"],
                                "pv20_u":payload["pv20_u"],
                                "pv19_u":payload["pv19_u"],
                                "pv15_u":payload["pv15_u"],
                                "a_u":payload["a_u"],
                                "reactive_power":payload["reactive_power"],
                                "pv17_u":payload["pv17_u"],
                                "c_u":payload["c_u"],
                                "mppt_8_cap":payload["mppt_8_cap"],
                                "pv20_i":payload["pv20_i"],
                                "pv15_i":payload["pv15_i"],
                                "efficiency":payload["efficiency"],
                                "pv17_i":payload["pv17_i"],
                                "pv11_i":payload["pv11_i"],
                                "pv13_i":payload["pv13_i"],
                                "pv11_u":payload["pv11_u"],
                                "mppt_power":payload["mppt_power"],
                                "pv13_u":payload["pv13_u"],
                                "run_state":payload["run_state"],
                                "close_time":payload["close_time"],
                                "pv19_i":payload["pv19_i"],
                                "mppt_7_cap":payload["mppt_7_cap"],
                                "mppt_5_cap":payload["mppt_5_cap"],
                                "pv27_u":payload["pv27_u"],
                                "pv2_i":payload["pv2_i"],
                                "active_power":payload["active_power"],
                                "pv4_i":payload["pv4_i"],
                                "pv6_i":payload["pv6_i"],
                                "pv8_i":payload["pv8_i"],
                                "mppt_6_cap":payload["mppt_6_cap"],
                                "pv27_i":payload["pv27_i"],
                                "pv1_u":payload["pv1_u"],
                                "pv3_u":payload["pv3_u"],
                                "pv23_i":payload["pv23_i"],
                                "pv5_u":payload["pv5_u"],
                                "pv25_i":payload["pv25_i"],
                                "pv7_u":payload["pv7_u"],
                                "pv23_u":payload["pv23_u"],
                                "inverter_state":payload["inverter_state"],
                                "pv9_u":payload["pv9_u"],
                                "pv25_u":payload["pv25_u"],
                                "total_cap":payload["total_cap"],
                                "b_i":payload["b_i"],
                                "mppt_3_cap":payload["mppt_3_cap"],
                                "pv21_u":payload["pv21_u"],
                                "mppt_10_cap":payload["mppt_10_cap"],
                                "pv16_u":payload["pv16_u"],
                                "pv18_u":payload["pv18_u"],
                                "temperature":payload["temperature"],
                                "bc_u":payload["bc_u"],
                                "b_u":payload["b_u"],
                                "pv21_i":payload["pv21_i"],
                                "elec_freq":payload["elec_freq"],
                                "mppt_4_cap":payload["mppt_4_cap"],
                                "pv16_i":payload["pv16_i"],
                                "pv18_i":payload["pv18_i"],
                                "day_cap":payload["day_cap"],
                                "pv12_i":payload["pv12_i"],
                                "pv14_i":payload["pv14_i"],
                                "pv12_u":payload["pv12_u"],
                                "mppt_1_cap":payload["mppt_1_cap"],
                                "pv14_u":payload["pv14_u"],
                                "pv10_u":payload["pv10_u"],
                                "pv26_u":payload["pv26_u"],
                                "pv1_i":payload["pv1_i"],
                                "pv28_u":payload["pv28_u"],
                                "pv3_i":payload["pv3_i"],
                                "mppt_2_cap":payload["mppt_2_cap"],
                                "pv5_i":payload["pv5_i"],
                                "ab_u":payload["ab_u"],
                                "ca_u":payload["ca_u"],
                                "pv7_i":payload["pv7_i"],
                                "pv10_i":payload["pv10_i"],
                                "pv9_i":payload["pv9_i"],
                                "sn":payload["sn"],
                                "station_code" :esn2station[data_item["sn"]]["plantCode"],
                            })
                        case 17:
                            for key in ["active_cap", "power_factor", "a_i", "c_i", "b_i", "reverse_reactive_valley", "positive_reactive_peak", "reverse_reactive_peak", "reverse_active_peak", "positive_active_peak", "a_u", "reactive_power", "c_u", "total_apparent_power", "bc_u", "b_u", "reverse_active_cap", "reverse_reactive_power", "positive_reactive_top", "active_power_b", "active_power_a", "positive_active_top", "reverse_reactive_cap", "positive_active_power", "positive_active_valley", "reverse_reactive_top", "reverse_active_power", "reverse_active_top", "reactive_power_a", "forward_reactive_cap", "reactive_power_b", "reactive_power_c", "reverse_active_valley", "active_power", "ab_u", "ca_u", "positive_reactive_power", "active_power_c", "grid_frequency", "positive_reactive_valley"]:
                                if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                                    payload[key] = 0
                            data_arr.append({
                                "dev_id" :payload["devId"],
                                "active_cap" :payload["active_cap"],
                                "power_factor" :payload["power_factor"],
                                "a_i" :payload["a_i"],
                                "c_i" :payload["c_i"],
                                "b_i" :payload["b_i"],
                                "reverse_reactive_valley" :payload["reverse_reactive_valley"],
                                "positive_reactive_peak" :payload["positive_reactive_peak"],
                                "reverse_reactive_peak" :payload["reverse_reactive_peak"],
                                "reverse_active_peak" :payload["reverse_active_peak"],
                                "positive_active_peak" :payload["positive_active_peak"],
                                "a_u" :payload["a_u"],
                                "reactive_power" :payload["reactive_power"],
                                "c_u" :payload["c_u"],
                                "total_apparent_power" :payload["total_apparent_power"],
                                "bc_u" :payload["bc_u"],
                                "b_u" :payload["b_u"],
                                "reverse_active_cap" :payload["reverse_active_cap"],
                                "reverse_reactive_power" :payload["reverse_reactive_power"],
                                "positive_reactive_top" :payload["positive_reactive_top"],
                                "active_power_b" :payload["active_power_b"],
                                "active_power_a" :payload["active_power_a"],
                                "positive_active_top" :payload["positive_active_top"],
                                "reverse_reactive_cap" :payload["reverse_reactive_cap"],
                                "positive_active_power" :payload["positive_active_power"],
                                "positive_active_valley" :payload["positive_active_valley"],
                                "reverse_reactive_top" :payload["reverse_reactive_top"],
                                "reverse_active_power" :payload["reverse_active_power"],
                                "reverse_active_top" :payload["reverse_active_top"],
                                "reactive_power_a" :payload["reactive_power_a"],
                                "forward_reactive_cap" :payload["forward_reactive_cap"],
                                "reactive_power_b" :payload["reactive_power_b"],
                                "reactive_power_c" :payload["reactive_power_c"],
                                "reverse_active_valley" :payload["reverse_active_valley"],
                                "active_power" :payload["active_power"],
                                "ab_u" :payload["ab_u"],
                                "ca_u" :payload["ca_u"],
                                "positive_reactive_power" :payload["positive_reactive_power"],
                                "active_power_c" :payload["active_power_c"],
                                "grid_frequency" :payload["grid_frequency"],
                                "positive_reactive_valley" :payload["positive_reactive_valley"],
                                "sn" :payload["sn"],
                                "station_code" :esn2station[data_item["sn"]]["plantCode"],
                            })
                        case 47:
                            for key in ["meter_status", "active_cap", "meter_i", "power_factor", "c_i", "meter_u", "b_i", "reverse_reactive_valley", "positive_reactive_peak", "reverse_reactive_peak", "reverse_active_peak", "positive_active_peak", "reactive_power", "c_u", "total_apparent_power", "bc_u", "b_u", "reverse_active_cap", "reverse_reactive_power", "positive_reactive_top", "active_power_b", "active_power_a", "positive_active_top", "reverse_reactive_cap", "positive_active_power", "positive_active_valley", "run_state", "reverse_reactive_top", "reverse_active_power", "reverse_active_top", "reactive_power_a", "forward_reactive_cap", "reactive_power_b", "reactive_power_c", "reverse_active_valley", "active_power", "ab_u", "ca_u", "positive_reactive_power", "active_power_c", "grid_frequency", "positive_reactive_valley"]:
                                if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                                    payload[key] = 0
                            data_arr.append({
                                "dev_id" :payload["devId"],
                                "meter_status" :payload["meter_status"],
                                "active_cap" :payload["active_cap"],
                                "meter_i" :payload["meter_i"],
                                "power_factor" :payload["power_factor"],
                                "c_i" :payload["c_i"],
                                "meter_u" :payload["meter_u"],
                                "b_i" :payload["b_i"],
                                "reverse_reactive_valley" :payload["reverse_reactive_valley"],
                                "positive_reactive_peak" :payload["positive_reactive_peak"],
                                "reverse_reactive_peak" :payload["reverse_reactive_peak"],
                                "reverse_active_peak" :payload["reverse_active_peak"],
                                "positive_active_peak" :payload["positive_active_peak"],
                                "reactive_power" :payload["reactive_power"],
                                "c_u" :payload["c_u"],
                                "total_apparent_power" :payload["total_apparent_power"],
                                "bc_u" :payload["bc_u"],
                                "b_u" :payload["b_u"],
                                "reverse_active_cap" :payload["reverse_active_cap"],
                                "reverse_reactive_power" :payload["reverse_reactive_power"],
                                "positive_reactive_top" :payload["positive_reactive_top"],
                                "active_power_b" :payload["active_power_b"],
                                "active_power_a" :payload["active_power_a"],
                                "positive_active_top" :payload["positive_active_top"],
                                "reverse_reactive_cap" :payload["reverse_reactive_cap"],
                                "positive_active_power" :payload["positive_active_power"],
                                "positive_active_valley" :payload["positive_active_valley"],
                                "run_state" :payload["run_state"],
                                "reverse_reactive_top" :payload["reverse_reactive_top"],
                                "reverse_active_power" :payload["reverse_active_power"],
                                "reverse_active_top" :payload["reverse_active_top"],
                                "reactive_power_a" :payload["reactive_power_a"],
                                "forward_reactive_cap" :payload["forward_reactive_cap"],
                                "reactive_power_b" :payload["reactive_power_b"],
                                "reactive_power_c" :payload["reactive_power_c"],
                                "reverse_active_valley" :payload["reverse_active_valley"],
                                "active_power" :payload["active_power"],
                                "ab_u" :payload["ab_u"],
                                "ca_u" :payload["ca_u"],
                                "positive_reactive_power" :payload["positive_reactive_power"],
                                "active_power_c" :payload["active_power_c"],
                                "grid_frequency" :payload["grid_frequency"],
                                "positive_reactive_valley" :payload["positive_reactive_valley"],
                                "sn" :payload["sn"],
                                "station_code" : esn2station[str(data_item["devId"])]["plantCode"]
                            })
            return data_arr
        except Exception as e:
            logging.error(f"convert device data error: {e}")

    def convertStationData(self,data):
        try:
            json_data = json.loads(data)
            data_arr = []
            pointer_list = "/data"
            data_list = resolve_pointer(json_data, pointer_list)
            for index, element in enumerate(data_list):
                pointer = f"/data/{index}"
                data_item = resolve_pointer(json_data, pointer)
                payload = {
                    **data_item["dataItemMap"],
                    "stationCode": int(data_item["stationCode"].split('=')[1]),
                }
                if data_item["dataItemMap"]:
                    for key in ['total_income', 'total_power', 'day_power', 'day_income', 'real_health_state', 'month_power']:
                        if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                            payload[key] = 0
                    data_arr.append({
                        'total_income': payload['total_income'],
                        'total_power': payload['total_power'],
                        'day_power': payload['day_power'],
                        'day_income': payload['day_income'],
                        'real_health_state': payload['real_health_state'],
                        'month_power': payload['month_power'],
                        'station_code': payload['stationCode']
                    })
            return data_arr
        except Exception as e:
            logging.error(f"convert station data error: {e}")

    def StationRealKpi(self,db: Session):
        
        urlGetStation = 'https://sg5.fusionsolar.huawei.com/thirdData/getStationRealKpi'
        if not self.xsrf_token:
            self.xsrf_token = self.getSolarApiToken()
        plantCode = self.listPlantCode()
        payload = {
            "stationCodes": plantCode
        }
        dataStation = self.requestsSolarAPI(payload, urlGetStation)
        if dataStation:
            db_handle.insertStation(self.convertStationData(dataStation),db)

    def convertStationSumData(self,data: str, period: str):
        try:
            json_data = json.loads(data)
            data_arr = []
            pointer_list = "/data"
            data_list = resolve_pointer(json_data, pointer_list)
            for index, element in enumerate(data_list):
                pointer = f"/data/{index}"
                data_item = resolve_pointer(json_data, pointer)
                collectTime = (data_item["collectTime"]/1000)
                stationCode = int(data_item["stationCode"].split('=')[1])
                payload = {
                    "collectTime": collectTime,
                    **data_item["dataItemMap"],
                    "stationCode": stationCode
                }
                if data_item["dataItemMap"]:
                    match period:
                        case 'hour':
                            for key in ['radiation_intensity', 'theory_power', 'inverter_power', 'ongrid_power', 'power_profit', 'stationCode']:
                                if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                                    payload[key] = 0
                            data_arr.append({
                                'collect_time' : payload['collectTime'],
                                'radiation_intensity' : round(payload['radiation_intensity'], 4),
                                'theory_power' : round(payload['theory_power'], 4),
                                'inverter_power' : round(payload['inverter_power'], 4),
                                'ongrid_power' : round(payload['ongrid_power'], 4),
                                'power_profit' : round(payload['power_profit'], 4),
                                'station_code' : payload['stationCode']
                            })
                        case 'day':
                            for key in ['inverter_power', 'selfUsePower', 'power_profit', 'perpower_ratio', 'reduction_total_co2', 'selfProvide', 'installed_capacity', 'use_power', 'reduction_total_coal', 'ongrid_power', 'buyPower', 'stationCode']:
                                if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                                    payload[key] = 0
                            data_arr.append({
                                'collect_time' : payload['collectTime'],
                                'inverter_power' : round(payload['inverter_power'], 4),
                                'self_use_power' : round(payload['selfUsePower'], 4),
                                'power_profit' : round(payload['power_profit'], 4),
                                'perpower_ratio' : round(payload['perpower_ratio'], 4),
                                'reduction_total_co2' : round(payload['reduction_total_co2'], 4),
                                'self_provide' : round(payload['selfProvide'], 4),
                                'installed_capacity' : round(payload['installed_capacity'], 4),
                                'use_power' : round(payload['use_power'], 4),
                                'reduction_total_coal' : round(payload['reduction_total_coal'], 4),
                                'ongrid_power' : round(payload['ongrid_power'], 4),
                                'buy_power' : round(payload['buyPower'], 4),
                                'station_code' : payload['stationCode']
                            })
                        case 'month':
                            for key in ['inverter_power', 'selfUsePower', 'power_profit', 'perpower_ratio', 'reduction_total_co2', 'selfProvide', 'installed_capacity', 'use_power', 'reduction_total_coal', 'ongrid_power', 'buyPower', 'stationCode']:
                                if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                                    payload[key] = 0
                            data_arr.append({
                                'collect_time' : payload['collectTime'],
                                'inverter_power' : round(payload['inverter_power'], 4),
                                'self_use_power' : round(payload['selfUsePower'], 4),
                                'power_profit' : round(payload['power_profit'], 4),
                                'perpower_ratio' : round(payload['perpower_ratio'], 4),
                                'reduction_total_co2' : round(payload['reduction_total_co2'], 4),
                                'self_provide' : round(payload['selfProvide'], 4),
                                'installed_capacity' : round(payload['installed_capacity'], 4),
                                'use_power' : round(payload['use_power'], 4),
                                'reduction_total_coal' : round(payload['reduction_total_coal'], 4),
                                'ongrid_power' : round(payload['ongrid_power'], 4),
                                'buy_power' : round(payload['buyPower'], 4),
                                'station_code' : payload['stationCode']})
                        case 'year':
                            for key in ['inverter_power', 'selfUsePower', 'reduction_total_tree', 'power_profit', 'perpower_ratio', 'reduction_total_co2', 'selfProvide', 'installed_capacity', 'use_power', 'reduction_total_coal', 'ongrid_power', 'buyPower', 'stationCode']:
                                if payload.get(key) is None or not isinstance(payload[key], (float, int)):
                                    payload[key] = 0
                            data_arr.append({
                                'collect_time' : payload['collectTime'],
                                'inverter_power' : round(payload['inverter_power'], 4),
                                'self_use_power' : round(payload['selfUsePower'], 4),
                                'reduction_total_tree' : round(payload['reduction_total_tree'], 4),
                                'power_profit' : round(payload['power_profit'], 4),
                                'perpower_ratio' : round(payload['perpower_ratio'], 4),
                                'reduction_total_co2' : round(payload['reduction_total_co2'], 4),
                                'self_provide' : round(payload['selfProvide'], 4),
                                'installed_capacity' : round(payload['installed_capacity'], 4),
                                'use_power' : round(payload['use_power'], 4),
                                'reduction_total_coal' : round(payload['reduction_total_coal'], 4),
                                'ongrid_power' : round(payload['ongrid_power'], 4),
                                'buy_power' : round(payload['buyPower'], 4),
                                'station_code' : payload['stationCode']})
            return data_arr
        except Exception as e:
            logging.error(f"convert station data error: {e}")



""" schedule.every(5).minutes.do(DevRealKpi)
schedule.every(5).minutes.do(StationRealKpi)
schedule.every().hours.do(Environment)
schedule.every().days.at("01:00").do(KpiStationDay)
schedule.every(30).days.do(KpiStationMonth)
schedule.every(30).days.do(KpiStationYear)

if __name__ == '__main__':
    DevList()
    KpiMsStation()
    StationsConf()
    EsnCode()
    DevRealKpi()
    KpiStationDay()
    KpiStationMonth()
    KpiStationYear()
    while True:
        schedule.run_pending()
        time.sleep(3) """
