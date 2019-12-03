from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template
from importlib.machinery import SourceFileLoader
from doreah.pyhp import file as pyhpfile
from . import db
#import auth
from doreah import auth
import pkg_resources
import os


WEBFOLDER = pkg_resources.resource_filename(__name__,"web")
STATICFOLDER = pkg_resources.resource_filename(__name__,"static")

def server_handlers(server):



	@server.get("/<file>.<ext>")
	def file(file,ext):
		return static_file(ext + "/" + file + "." + ext,root=STATICFOLDER)


	@server.get("/")
	def start():
		if auth.check(request):
			result = pyhpfile(os.path.join(WEBFOLDER,"main.pyhp"),{"db":db})
		else:
			#result = pyhpfile("web/login.pyhp",{"db":db,"auth":auth})
			result = auth.get_login_page(stylesheets=["/style.css"])

		return result


#	@server.get("/imgof/<uid>")
#	@auth.authenticated
#	def imageof(uid):
#		uid = int(uid)
#
#		obj = db.db.get(uid)
#		artwork = obj.get_artwork()
#		if artwork is None: return ""
#
#		mime,stream = artwork.read()
#		response.set_header('Content-type', mime)
#		response.set_header("Cache-Control", "public, max-age=360000")
#		return stream

	@server.get("/artwork/<uid>")
	@auth.authenticated
	def image(uid):
		try:
			uid = int(uid)
		except:
			return static_file("/static/png/unknown_" + uid + ".png",root="")

		artwork = db.db.get(uid)
		mime,stream = artwork.read()
		response.set_header('Content-type', mime)
		response.set_header("Cache-Control", "public, max-age=360000")
		return stream


	@server.get("/audioof/<uid>")
	@auth.authenticated
	def audioof(uid):

		uid = int(uid)

		obj = db.db.get(uid)
		audio = obj.get_audio()
		if audio is None: return ""

		mime,stream = audio.read()
		response.set_header('Content-type', mime)
		response.set_header("Cache-Control", "public, max-age=360000")
		return stream
