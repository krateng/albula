import server_api, server_web
import db
from threading import *
import time
import os



API_PORT = 42050
WEB_PORT = 42051
DIRECTORY = "../testlibrary/"




db.build_database(DIRECTORY)

thread_api = Thread(target=server_api.runserver,args=(API_PORT,))
thread_web = Thread(target=server_web.runserver,args=(WEB_PORT,))

thread_api.daemon = True
thread_web.daemon = True

thread_api.start()
thread_web.start()


def graceful_exit(sig=None,frame=None):
	print("Server shutting down...")
	os._exit(42)

#signal.signal(signal.SIGINT, graceful_exit)
#signal.signal(signal.SIGTERM, graceful_exit)

try:
    while True:
        time.sleep(10000)
except:
    graceful_exit()
