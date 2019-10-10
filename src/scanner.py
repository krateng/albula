from doreah.settings import get_settings
from doreah.io import NestedProgressBar
import os
import yaml
from db import Audio, Artwork


AUDIOFORMATS = ["mp3","flac"]
IMAGEFORMATS = ["jpeg","jpg","png","webp"]

class Directory:
	def __init__(self,name,subdirs,files):
		self.name = name
		self.subdirs = list(subdirs)
		self.files = list(files)

	def total_files(self):
		num = len(self.files)
		for sd in self.subdirs:
			num += sd.total_files()
		return num

# build directory tree
def scan_dir(dir,progressbar):
	subdirs = []
	files = []
	dirlist = os.listdir(dir)
	progressbar.godeeper(len(dirlist))
	for f in dirlist:
		if f in get_settings("IGNORE_FILES"):
			progressbar.done()
			return ([],[])
		if f.startswith("."):
			progressbar.progress(step=f)
			continue
		fullpath = os.path.join(dir,f)
		if os.path.isdir(fullpath):
			subdirs.append(Directory(f,*scan_dir(fullpath,progressbar)))
		else:
			ext = f.split(".")[-1].lower()
			if ext in AUDIOFORMATS: files.append(Audio(path=fullpath))
			elif ext in IMAGEFORMATS: files.append(Artwork(path=fullpath))
			elif f in ["artist.yml","artist.yaml"]:
				with open(fullpath,"r") as fil:
					files.append({**yaml.safe_load(fil),"type":"artist"})
			elif f in ["album.yml","album.yaml"]:
				with open(fullpath,"r") as fil:
					files.append({**yaml.safe_load(fil),"type":"album"})
			#else: print("File",f,"has unknown format")
			progressbar.progress(step=f)

	progressbar.done()
	return (subdirs,files)


def scan(dirs):
	scan_dir_prog = NestedProgressBar(len(dirs),prefix="Scanning directories",manual=True)
	results = []
	for dir in dirs:
		d = Directory(dir,*scan_dir(dir,progressbar=scan_dir_prog))
		results.append(d)

	return results
