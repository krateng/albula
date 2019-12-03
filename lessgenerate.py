import lesscpy
import os
from six import StringIO

LESS_FOLDER = "albula/static/less"
CSS_FILE = "albula/static/css/style.css"

less = ""
for f in os.listdir(LESS_FOLDER):
	with open(os.path.join(LESS_FOLDER,f),"r") as lessf:
		less += lessf.read()

css = lesscpy.compile(StringIO(less),minify=True)

with open(CSS_FILE,"w") as cssf:
	cssf.write(css)
