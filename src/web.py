from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template
from importlib.machinery import SourceFileLoader
from doreah.pyhp import file as pyhpfile
import db
import auth


def server_handlers(server):

	@server.get("/<file>.<ext>")
	def file(file,ext):
		return static_file("static/" + ext + "/" + file + "." + ext,root="")


	@server.get("/")
	def start():
		if auth.check(request):
			result = pyhpfile("web/main.pyhp",{"db":db})
		else:
			result = pyhpfile("web/login.pyhp",{"db":db,"auth":auth})

		return result


	@server.get("/imgof/<uid>")
	@auth.authenticated
	def imageof(uid):
		uid = int(uid)

		obj = db.db.get(uid)
		artwork = obj.get_artwork()
		if artwork is None: return ""

		mime,stream = artwork.read()
		response.set_header('Content-type', mime)
		return stream
