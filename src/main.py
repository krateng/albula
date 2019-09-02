from bottle import Bottle, run
import waitress
import web
import db
from threading import *
import time
import os



PORT = 42051
DIRECTORY = "../testlibrary/"





#db.build_database(DIRECTORY)

#thread_web = Thread(target=server.runserver,args=(PORT,))
#thread_web.daemon = True
#thread_web.start()






def graceful_exit(sig=None,frame=None):
	print("Server shutting down...")
	os._exit(42)

#signal.signal(signal.SIGINT, graceful_exit)
#signal.signal(signal.SIGTERM, graceful_exit)


server = Bottle()

db.api.mount(server=server)
web.server_handlers(server=server)

run(server, host='::', port=PORT, server='waitress')


#try:
#	while True:
#		time.sleep(10000)
#except:
#	graceful_exit()
