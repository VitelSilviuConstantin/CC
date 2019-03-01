import requests
import random
import json
import time
import configparser
from multiprocessing import Process

def make_request():
    random_ip = "{}.{}.{}.{}".format(str(random.randint(0, 255)), str(random.randint(0, 255)), \
                str(random.randint(0, 255)), str(random.randint(0, 255)))

    ip_req = "http://127.0.0.1:8000/index.html?ip={}".format(random_ip)
    req_obj = requests.get(ip_req)

    res_json = json.loads(req_obj.content)

    if res_json["status"] == "fail" or res_json['lat'] == '' or res_json['lon'] == '':
        return

    latitude = res_json["lat"]
    longitude = res_json["lon"]


    time_req = "http://127.0.0.1:8000/index.html?time=dummy"
    req_obj = requests.get(time_req)

    res_json = json.loads(req_obj.content)

    date = res_json["currentDateTime"][:10]
    new_year = str(int(date[0:4]) - 2)
    date = new_year + date[4:]

    config = configparser.ConfigParser()
    config.read("keyinfo.ini")
    key = config['API-KEY']['key']
    nasa_req = "http://127.0.0.1:8000/index.html?lat={}&lon={}&date={}&key={}".format(latitude, longitude, date, key)

    req_obj = requests.get(nasa_req)

def send_requests():
    proc_array = []

    for i in range(50):
        proc = Process(target = make_request)
        proc.start()
        proc_array.append(proc)

    for proc in proc_array:
        proc.join()

if __name__ == '__main__':
    send_requests()
    #make_request()