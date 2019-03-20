import server_api
import db

SERVER_PORT = 42050
WEB_PORT = 42051
DIRECTORY = "../testlibrary/"




db.build_database(DIRECTORY)

server_api.runserver(SERVER_PORT)
