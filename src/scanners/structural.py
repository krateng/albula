# scanner that takes folder structure into account

from db import db,Audio,Artwork,Album,Artist,Track,AUDIOFORMATS,IMAGEFORMATS

import os
import cleanup
import yaml
from doreah.settings import get_settings


class Directory:
	def __init__(self,name,subdirs,files):
		self.name = name
		self.subdirs = list(subdirs)
		self.files = list(files)

# build directory tree
def scan_dir(dir):
	subdirs = []
	files = []
	for f in os.listdir(dir):
		if f in get_settings("IGNORE_FILES"): return ([],[])
		if f.startswith("."): continue
		fullpath = os.path.join(dir,f)
		if os.path.isdir(fullpath):
			subdirs.append(Directory(f,*scan_dir(fullpath)))
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
			else: print("File",f,"has unknown format")

	return (subdirs,files)

def scan_tree(d):
	subdirs,files = d.subdirs, d.files

	# gather all audiofile references in this folder + subfolders (to check what this folder might be about)
	audiofiles = []
	for sd in subdirs:
		audiofiles += scan_tree(sd)


	info = []
	images = []
	for f in files:
		if isinstance(f,Audio):
			audiofiles.append({**f.metadata(),"obj":f})
		elif isinstance(f,Artwork):
			images.append(f)
		elif isinstance(f,dict):
			info.append(f)

	folder_album = None
	folder_artist = None

	folder_album_info = None
	folder_artist_info = None

	for inf in info:
		if inf.get("type") == "album":
			folder_album = ";".join(inf.get("albumartists")),inf.get("name")
			folder_album_info = inf
		if inf.get("type") == "artist":
			folder_artist = inf.get("name")
			folder_artist_info = inf


	# look at all files in this subtree and check if they seem to have an album or an
	# artist in common


	albums = {}
	artists = {}
	albumartists = {}
	for audio in audiofiles:
		albums[(audio["albumartist"],audio["album"])] = albums.setdefault((audio["albumartist"],audio["album"]),0) + 1
		albumartists[audio["albumartist"]] = albumartists.setdefault(audio["albumartist"],0) + 1
		artists[audio["albumartist"]] = artists.setdefault(audio["albumartist"],0) # set to 0 so it's there
		for artist in audio["artists"]:
			artists[artist] = artists.setdefault(artist,0) + 1
			albumartists[artist] = albumartists.setdefault(artist,0) # set to 0 so it's there


	artistlist = list(set(a for a in artists).union(set(a for a in albumartists)))
#	albumartistlist = [a for a in albumartists if albumartists[a] > len(audiofiles)/1.5]
	albumlist = [a for a in albums]

	artistlist.sort(key=lambda x:artists[x]+albumartists[x],reverse=True)
#	albumartistlist.sort(key=lambda x:albumartists[x],reverse=True)
	albumlist.sort(key=lambda x:albums[x],reverse=True)

	# if metadata lacks albumartist, assume it's the most common album with this
	# name in this subtree
#	for a in audiofiles:
#		if a["album"] is not None and a["albumartist"] is None:
#			samename = [alb for alb in albumlist if alb[1] == a["album"] and alb[0] is not None]
#			if len(samename) > 0:
#				a["albumartist"] = samename[0][0]


	# determine folder artist / album
	if folder_artist is None:
		if len(artistlist) > 0 and artists[artistlist[0]]+albumartists[artistlist[0]] > len(audiofiles)/1.5:
			#folder_artist = Artist(name=artistlist[0])
			folder_artist = artistlist[0]


	if folder_album is None:
		if len(albumlist) > 0 and albums[albumlist[0]] > len(audiofiles)/1.5:
			#print("common album",commonalbum)
			commonalbum = albumlist[0]
			#if commonalbum[0] is None: commonalbum = [],commonalbum[1]
			#commonalbum = cleanup.cleanartists(commonalbum[0]),commonalbum[1]
			if commonalbum[0] in [[],"",None]:
				# if most files have no album artist metadata, guess from tracks
				artists = {}
				count = 0
				#print(list(aud["albumartist"] for aud in audiofiles))
				for audio in audiofiles:
					if audio["albumartist"] in ["",None] and audio["album"] == commonalbum[1]:
						count += 1
						for a in audio["artists"]:
							artists[a] = artists.setdefault(a,0) + 1
				commonartists = []
				#print("artists",artists)
				artists_in_album = [a for a in artists]
		#		artists_in_album.sort(key=lambda x:artists[x],reverse=True)
				commonartists = [a for a in artists_in_album if artists[a] > count/2]
				if len(commonartists) == 0:
					commonartists = ["Various Artists"]
			#	while len(artists_in_album) > 0:
	#
	#				if artists[artists_in_album[0]] > count/2 or len(commonartists) == 0:
	#					commonartists.append(artists_in_album.pop(0))
	#					#print("adding, now",commonartists)
	#				else:
	#					break
				commonalbum = ";".join(commonartists), commonalbum[1]

			#folder_album = Album(name=commonalbum[1],albumartist=commonalbum[0])
			folder_album = commonalbum



	# go through tracks with missing data. assign folder album / artist
	for audio in audiofiles:

		if folder_album is not None and audio["album"] == folder_album[1] and audio["albumartist"] is None:
			audio["albumartist"] = folder_album[0]
		if folder_album is not None and audio["album"] is None and audio["albumartist"] is None:
			audio["albumartist"], audio["album"] = folder_album
		if folder_artist is not None and audio["artists"] is []:
			audio["artists"] = [folder_artist]



	## check artwork files

	for i in images:
		# if an image is here, just create the db object right now to append the artwork
		# so we don't need to carry this stuff up the function stack
		if "artist" in i.path.lower() and folder_artist is not None:
			a = Artist(name=cleanup.cleanartists([folder_artist])[0])
			if i not in a.artworks: a.artworks.append(i)
		elif "album" in i.path.lower() and folder_album is not None:

			a = Album(name=folder_album[1],albumartists=[Artist(name=a) for a in cleanup.cleanartists([folder_album[0]])])
			if i not in a.artworks: a.artworks.append(i)

		else: db.delete(i)

	return audiofiles





def build_database(dirs):
	scanned = 0

	#alreadydone = set(a.path for a in db.getall(Audio)).union(set(a.path for a in db.getall(Artwork)))
	for dir in dirs:

		d = Directory(dir,*scan_dir(dir))
		files = scan_tree(d)

		# all tracks that have no albumartist yet get their artist as albumartist
		# all tracks that have no album get their own title as album
		for f in files:
			if f["albumartist"] is None:
				#print("no albumartist:",f)
				f["albumartist"] = ", ".join(f["artists"])
			if f["album"] is None:
				f["album"] = f["title"]

		# create objects from metadata
		for f in files:
			aud = f["obj"]

			artists,title = cleanup.fullclean(f["artists"],f["title"])
			albumartists = cleanup.cleanartists([f["albumartist"]])


			track = Track(
				title=title,
				artists=[Artist(name=a) for a in artists],
				albums=[Album(name=f["album"],albumartists=[Artist(name=a) for a in albumartists])],
				audiofiles=[aud],
				length=f["length"]
			)

			# embedded artwork
			for aw in aud.get_embedded_artworks()["album"]:
				if aw not in track.albums[0].artworks:
						track.albums[0].artworks.append(aw)
