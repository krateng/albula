# non-relational db

from nimrodel import EAPI
import requests



#from db_oo_helper import Ref, MultiRef, DBObject, db, save_database, load_database
from doreah.database import Database, Ref, MultiRef
from doreah.settings import get_settings

db = Database(file="database.ddb")


class Artwork(db.DBObject):
	__primary__ = "path",
	path: str

	def read(self):
		if self.path.endswith(".jpeg") or self.path.endswith(".jpg"):
			mime = 'image/jpeg'
		elif self.path.endswith(".png"):
			mime = 'image/png'
		elif self.path.endswith(".webp"):
			mime = 'image/webp'
		with open(self.path,"rb") as imagefile:
			stream = imagefile.read()

		return mime,stream

class Audio(db.DBObject):
	__primary__ = "path",
	path: str

	def read(self):
		if self.path.endswith(".mp3"):
			mime = 'audio/mp3'
		elif self.path.endswith(".flac"):
			mime = 'audio/flac'
		with open(self.path,"rb") as audiofile:
			stream = audiofile.read()

		return mime,stream



class Album(db.DBObject):
	__primary__ = "name","albumartist"
	name: str
	albumartist: str
	artwork: list = MultiRef(Artwork,exclusive=False,backref="album")

	def __apidict__(self):
		return {
			"uid":self.uid,
			"albumartist":self.albumartist,
			"name":self.name,
			#"sorttitle":self.name.lower(),
			"artwork":[a.uid for a in self.artwork],
			"last_played":max(t.lastplayed for t in self.tracks),
			"times_played":sum(t.timesplayed for t in self.tracks),
			"track_ids":[track.uid for track in self.tracks]
		}

	def get_artwork(self):
		if len(self.artwork) > 0: return self.artwork[0]
		else: return None

class Artist(db.DBObject):
	__primary__ = "name",
	name: str
	artwork: list = MultiRef(Artwork,exclusive=False,backref="artist")

	def __apidict__(self):
		return {
			"uid":self.uid,
			"name":self.name,
			#"sorttitle":self.name.lower(),
			"artwork":[a.uid for a in self.artwork],
			"last_played":max(t.lastplayed for t in self.tracks),
			"times_played":sum(t.timesplayed for t in self.tracks),
			"track_ids":[track.uid for track in self.tracks]
		}

	def get_artwork(self):
		if len(self.artwork) > 0: return self.artwork[0]
		else: return None

	def get_tracklist(self):
		return self.tracks

class Track(db.DBObject):
	__primary__ = "title","artists"
	title: str
	artists: list = MultiRef(Artist,backref="tracks",exclusive=False)
	albums: list = MultiRef(Album,backref="tracks",exclusive=False)
	audiofiles: list = MultiRef(Audio,exclusive=True,backref="track")
	artwork: list = MultiRef(Artwork,exclusive=False,backref="track")
	length: int
	lastplayed: int
	timesplayed: int

	def __apidict__(self):
		return {
			"uid":self.uid,
			"title":self.title,
			"length":self.length,
			#"sorttitle":self.title.lower(),
			"artist_ids":list(a.uid for a in self.artists),
			"artist_names":list(a.name for a in self.artists),
			"artwork":[a.uid for a in self.artwork],
			"last_played":self.lastplayed,
			"times_played":self.timesplayed,
			"track_ids":[self.uid]
		}

	def get_artwork(self):
		if len(self.artwork) > 0: return self.artwork[0]
		else:
			for a in self.albums:
				if len(a.artwork) > 0: return a.artwork[0]
		return None

	def get_audio(self):
		if len(self.audiofiles) > 0: return self.audiofiles[0]
		return None

	def get_tracklist(self):
		return [self]





import auth

api = EAPI(path="api",delay=True,auth=auth.check)


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

def get_artwork_of(uid):
	obj = db.get(uid)
	artwork = obj.get_artwork()
	return artwork


@api.post("play")
def play_track(id:int,seconds:int,time:int):
	track = db.get(id)
	track.timesplayed += 1
	track.lastplayed = time

	if seconds > (track.length / 2):
		print("Scrobbling!")

		if get_settings("MALOJA_SCROBBLE"):
			server = get_settings("MALOJA_SERVER")
			key = get_settings("MALOJA_KEY")
			url = server + "/api/newscrobble"
			data = {
				"artist":"/".join(a.name for a in track.artists),
				"title":track.title,
				"duration":seconds,
				"time":time,
				"key":key
			}

		requests.post(url, data=data)

AUDIOFORMATS = ["mp3","flac"]
IMAGEFORMATS = ["jpeg","jpg","png"]

from scanners.simple import build_database

def save_database():
	db.save()
