from bottle import Bottle, run
import waitress
import web
import db
from threading import *
import time
import os
from doreah.settings import get_settings


HOST, PORT, DIRECTORIES = get_settings("HOST","PORT","MUSIC_DIRECTORIES")
THREADS = 12




#db.load_database()
db.build_database(DIRECTORIES)

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

#run(server, host='::', port=PORT, server='waitress',threads=24)
waitress.serve(server,host=HOST,port=PORT,threads=THREADS)


#try:
#	while True:
#		time.sleep(10000)
#except:
#	graceful_exit()
