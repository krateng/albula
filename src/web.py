from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template
from importlib.machinery import SourceFileLoader
from doreah.pyhp import file as pyhpfile
import db


def server_handlers(server):

	@server.get("/<file>.<ext>")
	def file(file,ext):
		return static_file("static/" + ext + "/" + file + "." + ext,root="")


	@server.get("/<name>")
	def page(name):
	#	session = db.Session()
		result = pyhpfile("web/" + name + ".pyhp",{"db":db})
	#	session.close()
		return result

	@server.get("/")
	def start():
	#	session = db.Session()
		result = pyhpfile("web/main.pyhp",{"db":db})
	#	session.close()
		return result


	@server.get("/imgof/<uid>")
	def imageof(uid):
		uid = int(uid)

		obj = db.db.get(uid)
		artwork = obj.get_artwork()
		if artwork is None: return ""

		mime,stream = artwork.read()
		response.set_header('Content-type', mime)
		return stream
