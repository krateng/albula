from doreah.settings import get_settings
from doreah.io import NestedProgressBar
import os
import yaml
from db import Audio, Artwork, Artist, Album


AUDIOFORMATS = ["mp3","flac"]
IMAGEFORMATS = ["jpeg","jpg","png","webp"]

class Directory:
	def __init__(self,name,subdirs=[],files=[]):
		self.name = name
		self.subdirs = list(subdirs)
		self.audiofiles = []
		self.imagefiles = []
		for f in files:
			if isinstance(f,Audio): self.audiofiles.append(f)
			elif isinstance(f,Artwork): self.imagefiles.append(f)

		self.artists = {}
		self.albums = {}
		self.artist = None
		self.album = None

	def add_file(self,f):
		if isinstance(f,Audio): self.audiofiles.append(f)
		elif isinstance(f,Artwork): self.imagefiles.append(f)

	def total_files(self):
		num = len(self.imagefiles) + len(self.audiofiles)
		for sd in self.subdirs:
			num += sd.total_files()
		return num

# build directory tree
def scan_dir(dir,progressbar):
	d = Directory(name=dir.split("/")[-1])

	dirlist = os.listdir(dir)
	progressbar.godeeper(len(dirlist))
	for f in dirlist:
		fullpath = os.path.join(dir,f)

		if f in get_settings("IGNORE_FILES"):
			break
		if f.startswith("."):
			progressbar.progress(step=f)
			continue
		if os.path.isdir(fullpath):
			d.subdirs.append(scan_dir(fullpath,progressbar))
		else:
			ext = f.split(".")[-1].lower()
			if ext in AUDIOFORMATS: d.add_file(Audio(path=fullpath))
			elif ext in IMAGEFORMATS: d.add_file(Artwork(path=fullpath))
			elif f in ["artist.yml","artist.yaml"]:
				with open(fullpath,"r") as fil:
					#files.append({**yaml.safe_load(fil),"type":"artist"})
					info = yaml.safe_load(fil)
					d.artist = Artist(name=info["name"])
			elif f in ["album.yml","album.yaml"]:
				with open(fullpath,"r") as fil:
					#files.append({**yaml.safe_load(fil),"type":"album"})
					info = yaml.safe_load(fil)
					d.album = Album(name=info["name"],albumartists=[Artist(name=a) for a in info["albumartists"]])

			#else: print("File",f,"has unknown format")
			progressbar.progress(step=f)

	progressbar.done()
	return d


def scan(dirs):
	scan_dir_prog = NestedProgressBar(len(dirs),prefix="Scanning directories",manual=True)
	results = []
	for dir in dirs:
		d = scan_dir(dir,progressbar=scan_dir_prog)
		results.append(d)

	return results
