# non-relational db

from nimrodel import EAPI
import os

import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

import cleanup

#from db_oo_helper import Ref, MultiRef, DBObject, db, save_database, load_database
from doreah.database import Database, Ref, MultiRef

db = Database(file="newdb.pck")


class Artwork(db.DBObject):
	path: str

class Audio(db.DBObject):
	path: str



class Album(db.DBObject):
	name: str
	albumartist: str
	artwork: list = MultiRef(Artwork,exclusive=False,backref="album")

	def __apidict__(self):
		return {
			"uid":self.uid,
			"albumartist":self.albumartist,
			"name":self.name,
			"artwork":[a.uid for a in self.artwork]
		}

	def get_artwork(self):
		if len(self.artwork) > 0: return "/img/albumart/" + str(self.artwork[0].uid)
		else: return ""

class Artist(db.DBObject):
	name: str
	artwork: list = MultiRef(Artwork,exclusive=False,backref="artist")

	def __apidict__(self):
		return {
			"uid":self.uid,
			"name":self.name,
			"artwork":[a.uid for a in self.artwork]
		}

	def get_artwork(self):
		if len(self.artwork) > 0: return "/img/artistart/" + str(self.artwork[0].uid)
		else: return ""

class Track(db.DBObject):
	title: str
	artists: list = MultiRef(Artist,backref="tracks",exclusive=False)
	albums: list = MultiRef(Album,backref="tracks",exclusive=False)
	audiofiles: list = MultiRef(Audio,exclusive=True,backref="track")
	artwork: list = MultiRef(Artwork,exclusive=False,backref="track")

	def __apidict__(self):
		return {
			"uid":self.uid,
			"title":self.title,
			"artists":self.artists,
			"artwork":[a.uid for a in self.artwork]
		}

	def get_artwork(self):
		if len(self.artwork) > 0: return "/img/trackart/" + str(self.artwork[0].uid)
		else:
			for a in self.albums:
				if len(a.artwork) > 0: return "/img/albumart/" + str(a.artwork[0].uid)
		return ""



db.done()

if False:
	bp = Artist(name="Blackpink")
	ex = Artist(name="EXID")
	rv = Artist(name="Red Velvet")
	ay = Album(name="Ah Yeah",albumartist="EXID")
	st = Album(name="Square Three",albumartist="BLACKPINK")
	AAIYL = Track(title="As If It's Your Last",artists=[bp],albums=[st])
	mash = Track(title="Megamashup 2019",artists=[rv,bp,ex],albums=[ay])






api = EAPI(path="api",delay=True)


@api.get("artists")
def list_artists():
	return db.getall(Artist)

@api.get("albums")
def list_albums():
	return db.getall(Album)

@api.get("tracks")
def list_tracks():
	return db.getall(Track)


@api.get("artist/{id}")
def get_artist(id:int):
	artist = db.get(id)
	result = {}
	result["artist"] = artist
	result["tracks"] = artist.tracks
	result["albums"] = []
	for t in result["tracks"]:
		result["albums"] += t.albums
	result["albums"] = list(set(result["albums"]))

	return result


@api.get("album/{id}")
def get_album(id:int):
	album = db.get(id)
	result = {}
	result["album"] = album
	result["tracks"] = album.tracks
	# sort artists by presence on this album
	artisttracks = {}
	for t in result["tracks"]:
		for a in t.artists:
			artisttracks[a] = artisttracks.setdefault(a,0) + 1
	result["artists"] = sorted([a for a in artisttracks],key=lambda x: artisttracks[x],reverse=True)
	#result["artists"] = list(set(a for t in result["tracks"] for a in t.artists))

	return result


def get_file_by_ref(uid):
	#print("getting file path for uid",uid)
	path = db.get(uid).path
	return path



def build_database(dirs):


	scanned = 0

	pics_album = []
	pics_artist = []
	# temporary pic storage. we need to wait til we have all the music files so we can match them

	alreadydone = set(a.path for a in db.getall(Audio))

	for dir in dirs:
		for (root,dirs,files) in os.walk(dir,followlinks=True):
			for f in files:
				#print("Scanning file",f)
				scanned += 1
				if scanned % 100 == 0:
					print(scanned,"files scanned...")
				fullpath = os.path.join(dir,root,f)
				if fullpath in alreadydone: continue
				ext = f.split(".")[-1].lower()


				### AUDIO FILES
				if ext in ["flac","mp3"]:

					embedded_pictures = {}

					if ext in ["flac"]:
						audio = FLAC(fullpath)

						tags = audio.tags
						try:
							album = [entry[1] for entry in tags if entry[0] == "ALBUM"][0]
						except:
							album = "Unknown Album"
						try:
							title = [entry[1] for entry in tags if entry[0] == "TITLE"][0]
						except:
							title = f
						artists = [entry[1] for entry in tags if entry[0] == "ARTIST"]
						try:
							albumartist = [entry[1] for entry in tags if entry[0] == "ALBUMARTIST"][0]
						except:
							albumartist = ", ".join(artists)


						imgs = audio.pictures
						for i in imgs:
							if i.type == 3:
								embedded_pictures["album"] = (hash(i.data),i.mime,i.data)



					elif ext in ["mp3"]:
						audio = MP3(fullpath)

						tags = audio.tags
						try:
							album = tags.get("TALB").text[0]
						except:
							album = "Unknown Album"
						try:
							title = tags.get("TIT2").text[0]
						except:
							title = f

						imgs = tags.getall("APIC")
						for i in imgs:
							if i.type == 3:
								embedded_pictures["album"] = (hash(i.data),i.mime,i.data)


						#artists = [set(obj.text) for obj in tags.getall("TPE1") + tags.getall("TPE2") + tags.getall("TPE3") + tags.getall("TPE4")]
						artists = [set(obj.text) for obj in tags.getall("TPE1")]
						artists = set.union(*artists)
						try:
							albumartist = tags.get("TPE2").text[0]
						except:
							albumartist = ", ".join(artists)


					# extract track from file and add to database
					artists,title = cleanup.fullclean(artists,title)
					track = add_of_find_existing_track(title=title,artists=artists,album=album,albumartist=albumartist,file=fullpath)

					if "album" in embedded_pictures:
						imghash,mime,data = embedded_pictures["album"]
						imagefile = str(imghash) + "." + mime.split("/")[-1]
						if not os.path.exists("cache/" + imagefile):
							with open("cache/" + imagefile,"wb") as fi:
								fi.write(data)
							#ref = AlbumArtRef(album_id=track.album.uid,path="cache/" + imagefile)
							track.albums[0].artwork.append(Artwork(path="cache/" + imagefile))


				### ARTWORK FILES
				elif ext in ["png","jpg","jpeg","webp"]:

					if "album" in f:
						pics_album.append(fullpath)

					elif "artist" in f:
						pics_artist.append(fullpath)


				### OTHER
				else:
					print("File",f,"has unknown format")





	# after all audio files are scanned, check our scanned artwork files and see if they
	# can be matched with a track

	for img in pics_album:
		imgpath = "/".join(img.split("/")[:-1])
		# find ALL tracks in folders and subfolders
		album_occurences = {}
		for result in [audio for audio in db.getall(Audio) if audio.path.startswith(imgpath)]:
			#print("getting albums of track",result.path)
			#print(result.__dict__)
			#print(result)
			albums = result.track.albums
			for a in albums:
				album_occurences[a] = album_occurences.get(a,0) + 1

		try:
			album = sorted([a for a in album_occurences],key=lambda x: album_occurences[x],reverse=True)[0]
			album.artwork.append(Artwork(path=img))
		except:
			pass

	for img in pics_artist:
		imgpath = "/".join(img.split("/")[:-1])
		# find ALL tracks in folders and subfolders
		artist_occurences = {}
		for result in [audio for audio in db.getall(Audio) if audio.path.startswith(imgpath)]:
			artists = result.track.artists
			for a in artists:
				artist_occurences[a] = artist_occurences.get(a,0) + 1

		try:
			artist = sorted([a for a in artist_occurences],key=lambda x: artist_occurences[x],reverse=True)[0]
			artist.artwork.append(Artwork(path=img))
		except:
			pass


	db.save()





def add_of_find_existing_track(title,artists,album,albumartist,file):



	albumobj = add_of_find_existing_album(album,albumartist)
	artistobjs = [add_of_find_existing_artist(artist) for artist in artists]

	for t in db.getall(Track):
		if t.artists == artistobjs and t.title == title:
			trackobj = t
			break
	else:
		trackobj = Track(title=title,albums=[albumobj],artists=artistobjs)

	trackobj.audiofiles.append(Audio(path=file))

	return trackobj

def add_of_find_existing_album(name,artist):

	for a in db.getall(Album):
		if a.name.lower() == name.lower() and a.albumartist.lower() == artist.lower():
			return a

	albumobj = Album(name=name,albumartist=artist)
	return albumobj

def add_of_find_existing_artist(name):

	for a in db.getall(Artist):
		if a.name.lower() == name.lower():
			return a

	artistobj = Artist(name=name)
	return artistobj
