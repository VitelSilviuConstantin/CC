from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import parse
import requests
import sqlite3
import time
import json
import re
import cgi

def create_database():
    conn = sqlite3.connect('actors_and_movies.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE actors
                    (id text, full_name text, age text)''')
    cursor.execute('''CREATE TABLE movies
                    (id text, id_actor text, name text, budget real, release_date text)''')


def insert_into_actors(id, full_name, age):
    conn = sqlite3.connect('actors_and_movies.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO actors VALUES (\'{}\', \'{}\', \'{}\')'.format(id, full_name, age))
    conn.commit()
    conn.close()

def insert_into_movies(id, id_actor, name, budget, release_date):
    conn = sqlite3.connect('actors_and_movies.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO movies VALUES (\'{}\', \'{}\', \'{}\', \'{}\', \'{}\')'.format(id, id_actor, name, budget, release_date))
    conn.commit()
    conn.close()


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        route_to_function_dict = {
            "/actors$" : self.getActors,
            "/actors/[0-9]+$" : self.getActor,
            "/actors/[0-9]+/movies$" : self.getMovies,
            "/actors/[0-9]+/movies/[0-9]+$" : self.getMovie
        }

        route_found = False

        for route in route_to_function_dict:
            if re.match(route, self.path):
                route_found = True
                route_to_function_dict[route]()

        if not route_found:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("Error 404!", 'utf-8'))

    def do_POST(self):
        if self.headers.get('content-type') is None:
            self.send_response(415)
            self.end_headers()
            return

        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        print(ctype)

        if ctype != 'application/json':
            self.send_response(215)
            self.end_headers()
            return

        route_to_function_dict = {
            "/actors$": self.addActor,
            "/actors/[0-9]+/movies$": self.addMovie
        }

        route_found = False

        for route in route_to_function_dict:
            if re.match(route, self.path):
                route_found = True
                route_to_function_dict[route]()

        if not route_found:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("Error 404!", 'utf-8'))

    def do_PUT(self):
        if self.headers.get('content-type') is None:
            self.send_response(415)
            self.end_headers()
            return

        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        print(ctype)

        if ctype != 'application/json':
            self.send_response(215)
            self.end_headers()
            return

        route_to_function_dict = {
            "/actors$": self.updateActor,
            "/actors/[0-9]+/movies$": self.updateMovie
        }

        route_found = False

        for route in route_to_function_dict:
            if re.match(route, self.path):
                route_found = True
                route_to_function_dict[route]()

        if not route_found:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("Error 404!", 'utf-8'))

    def do_DELETE(self):
        route_to_function_dict = {
            "/actors/[0-9]+$": self.deleteActor,
            "/actors/[0-9]+/movies/[0-9]+$": self.deleteMovie
        }

        route_found = False

        for route in route_to_function_dict:
            if re.match(route, self.path):
                route_found = True
                route_to_function_dict[route]()

        if not route_found:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("Error 404!", 'utf-8'))

    def getActors(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        dict_actors_list = []

        for entry in cursor.execute('SELECT * FROM actors'):
            dict_actor = {"ID":entry[0], "Full_name":entry[1], "Age":entry[2]}
            dict_actors_list.append(dict_actor)

        result_dict = {"Actors":dict_actors_list}
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(json.dumps(result_dict), 'utf-8'))

    def getActor(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        id = self.path.split("/")[2]

        actor_entry = cursor.execute('SELECT * FROM actors WHERE id=?', id).fetchone()

        if actor_entry is None:
            self.send_response(404)
            self.end_headers()
        else:
            result_dict = {"ID": actor_entry[0], "Full_name": actor_entry[1], "Age": actor_entry[2]}
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result_dict, indent=4), 'utf-8'))


    def getMovies(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        id = self.path.split("/")[2]
        dict_movies_list = []

        for entry in cursor.execute("SELECT * FROM movies WHERE id_actor=?", id):
            dict_movie = {"ID": entry[0], "ID_actor": entry[1], "Name": entry[2],
                          "budget":entry[3], "release_date":entry[4]}
            dict_movies_list.append(dict_movie)

        result_dict = {"Movies": dict_movies_list}
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(json.dumps(result_dict), 'utf-8'))


    def getMovie(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        id_actor = self.path.split("/")[2]
        id_movie = self.path.split("/")[4]

        movie_entry = cursor.execute('SELECT * FROM movies WHERE id=:id AND id_actor=:id_actor',
                                     {"id":id_movie, "id_actor":id_actor}).fetchone()

        if movie_entry is None:
            self.send_response(404)
            self.end_headers()
        else:
            result_dict = {"ID": movie_entry[0], "ID_actor": movie_entry[1], "Name": movie_entry[2],
                          "budget":movie_entry[3], "release_date":movie_entry[4]}
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result_dict), 'utf-8'))

    def addActor(self):
        length = int(self.headers.get('content-length'))
        input_dict = json.loads(self.rfile.read(length))

        if len(input_dict.keys()) != 3 or set(input_dict.keys()) != set(["ID", "Full_name", "Age"]):
            self.send_response(400)
            self.end_headers()
            return

        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        actor_entry = cursor.execute('SELECT * FROM actors WHERE id=?', input_dict["ID"]).fetchone()

        if actor_entry:
            self.send_response(409)
            self.end_headers()
            return

        insert_into_actors(input_dict["ID"], input_dict["Full_name"], input_dict["Age"])
        self.send_response(201)
        self.end_headers()

    def addMovie(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        length = int(self.headers.get('content-length'))
        input_dict = json.loads(self.rfile.read(length))

        id_actor = self.path.split("/")[2]

        actor_entry = cursor.execute('SELECT * FROM actors WHERE id=?', id_actor).fetchone()

        if actor_entry is None:
            self.send_response(404)
            self.end_headers()
            return

        if len(input_dict.keys()) != 4 or set(input_dict.keys()) != set(["ID", "Name", "Budget", "Release_date"]):
            self.send_response(400)
            self.end_headers()
            return

        movie_entry = cursor.execute('SELECT * FROM movies WHERE id=?', input_dict["ID"]).fetchone()

        if movie_entry:
            self.send_response(409)
            self.end_headers()
            return

        insert_into_movies(input_dict["ID"], id_actor, input_dict["Name"], input_dict["Budget"], input_dict["Release_date"])
        self.send_response(201)
        self.end_headers()

    def updateActor(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        length = int(self.headers.get('content-length'))
        input_dict = json.loads(self.rfile.read(length))

        if len(input_dict.keys()) != 3 or set(input_dict.keys()) != set(["ID", "Field", "Value"]):
            self.send_response(400)
            self.end_headers()
            return

        actor_entry = cursor.execute('SELECT * FROM actors WHERE id=?', input_dict["ID"]).fetchone()

        if not actor_entry:
            self.send_response(404)
            self.end_headers()
            return

        cursor.execute('UPDATE actors SET {} = \'{}\' WHERE id = {}'.format(input_dict["Field"],
                                                                        input_dict["Value"], input_dict["ID"]))

        conn.commit()
        conn.close()

        self.send_response(200)
        self.end_headers()

    def updateMovie(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        id_actor = self.path.split("/")[2]

        actor_entry = cursor.execute('SELECT * FROM actors WHERE id=?', id_actor).fetchone()

        if not actor_entry:
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('content-length'))
        input_dict = json.loads(self.rfile.read(length))

        if len(input_dict.keys()) != 3 or set(input_dict.keys()) != set(["ID", "Field", "Value"]):
            self.send_response(400)
            self.end_headers()
            return

        movie_entry = cursor.execute('SELECT * FROM movies WHERE id=:id_movie AND id_actor=:id_actor',
                                     {'id_movie':input_dict["ID"], 'id_actor':id_actor}).fetchone()

        if not movie_entry:
            self.send_response(404)
            self.end_headers()
            return

        cursor.execute('''UPDATE movies SET {0} = \"{1}\" WHERE id = {2}'''.format(input_dict["Field"],
                                                                            input_dict["Value"], input_dict["ID"]))

        conn.commit()
        conn.close()

        self.send_response(200)
        self.end_headers()

    def deleteActor(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        id_actor = self.path.split("/")[2]

        actor_entry = cursor.execute('SELECT * FROM actors WHERE id=?', id_actor).fetchone()

        if not actor_entry:
            self.send_response(404)
            self.end_headers()
            return

        cursor.execute('DELETE FROM actors WHERE id=?', id_actor)

        conn.commit()
        conn.close()

        self.send_response(200)
        self.end_headers()

    def deleteMovie(self):
        conn = sqlite3.connect('actors_and_movies.db')
        cursor = conn.cursor()

        id_actor = self.path.split("/")[2]

        actor_entry = cursor.execute('SELECT * FROM actors WHERE id=?', id_actor).fetchone()

        if not actor_entry:
            self.send_response(404)
            self.end_headers()
            return

        id_movie = self.path.split("/")[4]

        movie_entry = cursor.execute('SELECT * FROM movies WHERE id=:id_movie AND id_actor=:id_actor',
                                     {'id_movie': id_movie, 'id_actor': id_actor}).fetchone()

        if not movie_entry:
            self.send_response(404)
            self.end_headers()
            return

        cursor.execute('DELETE FROM movies WHERE id=:id_movie AND id_actor=:id_actor',
                       {"id_movie":id_movie, "id_actor":id_actor})

        conn.commit()
        conn.close()

        self.send_response(200)
        self.end_headers()

def run_server():
    httpd = HTTPServer(('localhost', 8000), Server)
    httpd.serve_forever()

run_server()

#insert_into_actors("3", "Ben Affleck", 46)
#insert_into_actors("4", "Jessica Chastain", 41)
#insert_into_actors("5", "Margot Robbie", 28)

#insert_into_movies("3", "3", "Batman v. Superman: Dawn of Justice", "300", "25-03-2016")
#insert_into_movies("4", "4", "Interstellar", "200", "07-11-2014")
#insert_into_movies("5", "5", "The Wolf of Wall Street", "500", "25-12-2013")