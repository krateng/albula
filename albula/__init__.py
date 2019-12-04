### PACKAGE DATA

__name__ = "albula"
__desc__ = "A minimalist self-hosted music server."
__version__ = 0,5,2
__versionstr__ = ".".join(str(n) for n in __version__)
__author__ = {
	"name":"Johannes Krattenmacher",
	"email":"albula@krateng.dev",
	"github":"krateng"
}

__requires__ = [
	"bottle>=0.12.16",
	"waitress>=1.3",
	"doreah>=1.2.10",
	"nimrodel>=0.6.1",
	"mutagen>=1.42",
	"pyyaml>=5.1",
	"lesscpy>=0.13"
]
__resources__ = [
	"web/*/*",
	"web/*",
	"static/*/*",
	"data_files/*/*"
]

__commands__ = {
	"albula":"controller:main"
}

### DOREAH CONFIGURATION

from doreah import config
config(
	logging={
		"logfolder": "logs"
	},
	settings={
		"files":[
			"settings/default.ini",
			"settings/settings.ini"
		]
	},
	auth={
		"multiuser": False,
		"cookieprefix": "albula"
	}
)


### USER DATA FOLDER


import os
import pkg_resources
from distutils import dir_util

try:
	DATA_DIR = os.environ["XDG_DATA_HOME"].split(":")[0]
	assert os.path.exists(DATA_DIR)
except:
	DATA_DIR = os.path.join(os.environ["HOME"],".local/share/")

DATA_DIR = os.path.join(DATA_DIR,"albula")
os.makedirs(DATA_DIR,exist_ok=True)



def copy_initial_local_files():
	folder = pkg_resources.resource_filename(__name__,"data_files")
	#shutil.copy(folder,DATA_DIR)
	dir_util.copy_tree(folder,DATA_DIR)

copy_initial_local_files()
