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



#    html = "<html>"
#    html += "<head>"
#    with open("static/html/common_head.html","r") as common_head:
#        html += common_head.read()
#    html += "</head><body>"
#    with open("static/html/common_header.html","r") as common_header:
#        html += common_header.read()
#    for y in SourceFileLoader(name,"web/" + name + ".py").load_module().page():
#        html += y + "\n"
#
#    html += "</body></html>"
#    return html
