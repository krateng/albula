from doreah.settings import get_settings
from doreah.io import NestedProgressBar, ProgressBar
import os
import yaml
from ..db import Audio, Artwork, Artist, Album, Track, db


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
	old_audiofiles = db.getall(Audio)
	for a in old_audiofiles:
		if not os.path.exists(a.path):
			a.track.audiofiles.remove(a)
			db.delete(a)


	scan_dir_prog = NestedProgressBar(len(dirs),prefix="Scanning directories",manual=True)
	trees = []
	new_audiofiles = []
	for dir in dirs:
		d = scan_dir(dir,progressbar=scan_dir_prog)
		trees.append(d)

	new_audiofiles = [a for a in db.getall(Audio) if a not in old_audiofiles]

	old_tracks = db.getall(Track)

	#when scanning, also call metadata refresher for newly added files
	from ..dbbuild.parser import build_metadata
	build_metadata(new_audiofiles,trees)

	new_tracks = [t for t in db.getall(Track) if t not in old_tracks]

	# import maloja data for new tracks
	malserver = get_settings("MALOJA_SERVER")
	if malserver is not None:
		from ..dbbuild.malojareader import get_scrobbles
		get_scrobbles(new_tracks)


	from ..dbbuild.pruner import prune_database
	prune_database()

	return trees
