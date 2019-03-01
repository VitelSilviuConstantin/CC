from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import parse
import requests
import sqlite3
import time
import json
import configparser

def create_database():
    conn = sqlite3.connect('requests.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE requests
                    (api text, data text, req text, response text, latency real)''')


def insert_into_db(api, date, req, response, latency):
    conn = sqlite3.connect('requests.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO requests VALUES (\'{}\', \'{}\', \'{}\', \'{}\', {})'.format(api, date, req, response, latency))
    conn.commit()
    conn.close()

def get_db_info():
    conn = sqlite3.connect('requests.db')
    cursor = conn.cursor()

    for entry in cursor.execute('SELECT * FROM requests'):
        print(entry)


def get_metrics():
    conn = sqlite3.connect('requests.db')
    cursor = conn.cursor()

    sum_time = cursor.execute('SELECT SUM(latency) FROM requests WHERE api=\'ip\'').fetchone()
    req_nr = cursor.execute('SELECT COUNT(*) FROM requests WHERE api=\'ip\'').fetchone()
    ip_time_avg = sum_time[0]/req_nr[0]

    sum_time = cursor.execute('SELECT SUM(latency) FROM requests WHERE api=\'time\'').fetchone()
    req_nr = cursor.execute('SELECT COUNT(*) FROM requests WHERE api=\'time\'').fetchone()
    time_time_avg = sum_time[0] / req_nr[0]

    sum_time = cursor.execute('SELECT SUM(latency) FROM requests WHERE api=\'nasa\'').fetchone()
    req_nr = cursor.execute('SELECT COUNT(*) FROM requests WHERE api=\'nasa\'').fetchone()
    nasa_time_avg = sum_time[0] / req_nr[0]

    return {"ip_avg" : ip_time_avg, "time_avg" : time_time_avg,"nasa_avg" : nasa_time_avg}

class Server(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'

        sp_res = parse.urlsplit(self.path)

        if sp_res.path == '/index.html':
            if sp_res.query == '':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(open('index.html').read(), 'utf-8'))
            else:
                get_params_dict = parse.parse_qs(sp_res.query)
                if 'ip' in get_params_dict:
                    ip_api_request = "http://extreme-ip-lookup.com/json/{}".format(get_params_dict['ip'][0])
                    req_obj = requests.get(ip_api_request)
                    insert_into_db('ip', time.strftime("%Y-%m-%d", time.localtime()), ip_api_request,
                                   str(req_obj.status_code), req_obj.elapsed.total_seconds())
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(req_obj.content)

                if 'time' in get_params_dict:
                    time_api_request = "http://worldclockapi.com/api/json/est/now"
                    req_obj = requests.get(time_api_request)
                    insert_into_db('time', time.strftime("%Y-%m-%d", time.localtime()), time_api_request,
                                   str(req_obj.status_code), req_obj.elapsed.total_seconds())
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(req_obj.content)

                if 'lat' in get_params_dict:
                    nasa_api_request = "https://api.nasa.gov/planetary/earth/imagery/?lon={}&lat={}&date={}" \
                                       "&api_key={}".format(get_params_dict['lon'][0], get_params_dict['lat'][0],
                                                                  get_params_dict['date'][0], get_params_dict['key'][0])
                    req_obj = requests.get(nasa_api_request)
                    insert_into_db('nasa', time.strftime("%Y-%m-%d", time.localtime()), nasa_api_request,
                                   str(req_obj.status_code), req_obj.elapsed.total_seconds())
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(req_obj.content)

                if 'ip_full' in get_params_dict:
                    ip_api_request = "http://extreme-ip-lookup.com/json/{}".format(get_params_dict['ip_full'][0])
                    req_obj = requests.get(ip_api_request)
                    ip_json = json.loads(req_obj.content)

                    if ip_json["status"] == "fail":
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'<html><body>Eroare sefu!<body><html>')
                        return

                    latitude = ip_json['lat']
                    longitude = ip_json['lon']

                    if latitude == "" or longitude == "":
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'<html><body>N-are locatie sefu!<body><html>')
                        return

                    time_api_request = "http://worldclockapi.com/api/json/est/now"
                    req_obj = requests.get(time_api_request)
                    time_json = json.loads(req_obj.content)
                    date = time_json["currentDateTime"][:10]
                    new_year = str(int(date[0:4]) - 2)
                    date = new_year + date[4:]

                    config = configparser.ConfigParser()
                    config.read("keyinfo.ini")
                    key = config['API-KEY']['key']
                    nasa_api_request = "https://api.nasa.gov/planetary/earth/imagery/?lon={}&lat={}&date={}" \
                                       "&api_key={}".format(longitude, latitude, date, key)
                    req_obj = requests.get(nasa_api_request)
                    nasa_json = json.loads(req_obj.content)

                    if 'url' not in nasa_json:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'<html><body>N-am gasit poza sefu!<body><html>')

                    else:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(bytes('<html><body><img src=\"{}\"<body><html>'.format(nasa_json['url']), 'utf-8'))


        elif sp_res.path == "/metrics":
            metrics_dict = get_metrics()
            html = "<html><body>Avg response time for IP geolocation API: {}<br>" \
                    "Average response time for time API: {}<br>" \
                   "Average response time for NASA API: {} </body></html>".format(round(metrics_dict['ip_avg'], 2),
                                                                                  round(metrics_dict['time_avg'], 2),
                                                                                  round(metrics_dict['nasa_avg'], 2))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes(html, "utf-8"))



def run_server():
    httpd = HTTPServer(('localhost', 8000), Server)
    httpd.serve_forever()

run_server()
#get_db_info()
#get_metrics()