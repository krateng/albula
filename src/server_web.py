from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template
import waitress
from importlib.machinery import SourceFileLoader


import db


webserver = Bottle()

@webserver.get("/<file>.<ext>")
def file(file,ext):
    return static_file("static/" + ext + "/" + file + "." + ext,root="")

@webserver.get("/<name>")
def page(name):
    html = "<html>"
    html += "<head>"
    with open("static/html/common_head.html","r") as common_head:
        html += common_head.read()
    html += "</head><body>"
    with open("static/html/common_header.html","r") as common_header:
        html += common_header.read()
    for y in SourceFileLoader(name,"web/" + name + ".py").load_module().page():
        html += y + "\n"

    html += "</body></html>"
    return html




def runserver(port):
    run(webserver, host='::', port=port, server='waitress')
