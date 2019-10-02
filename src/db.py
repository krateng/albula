# non-relational db

from nimrodel import EAPI
import requests
import os

import random


import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import zlib


#from db_oo_helper import Ref, MultiRef, DBObject, db, save_database, load_database
from doreah.database import Database, Ref, MultiRef
from doreah.settings import get_settings

db = Database(file="database.ddb",ignore_capitalization=True)


class Artwork(db.DBObject):
	__primary__ = "path",
	path: str

	def read(self):
		if self.path.lower().endswith(".jpeg") or self.path.lower().endswith(".jpg"):
			mime = 'image/jpeg'
		elif self.path.lower().endswith(".png"):
			mime = 'image/png'
		elif self.path.lower().endswith(".webp"):
			mime = 'image/webp'
		with open(self.path,"rb") as imagefile:
			stream = imagefile.read()

		return mime,stream

	def link(self):
		return "/artwork/" + str(self.uid)

# if no artwork is present, return default file
class PA:
	def __init__(self,type):
		self.type = type
	def link(self):
		return "/artwork/" + self.type

pseudoartworks = {"artist":PA("artist"),"album":PA("album"),"track":PA("track")}
def PseudoArtwork(type):
	return pseudoartworks[type]




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


	# extracts artwork, saves it and returns reference
	def get_embedded_artworks(self):
		ext = self.path.split(".")[-1].lower()
		if ext in ["flac"]:
			audio = FLAC(self.path)
			imgs = audio.pictures

		elif ext in ["mp3"]:
			audio = MP3(self.path)
			tags = audio.tags
			imgs = tags.getall("APIC")

		artworks = {"album":[],"track":[],"artist":[]}
		for i in imgs:

			data = i.data
			imghash = str(zlib.adler32(data))
			mime = i.mime

			imagefile = imghash[:3] + "/" + imghash[3:] + "." + mime.split("/")[-1]
			artwork = Artwork(path="cache/" + imagefile)
			if not os.path.exists("cache/" + imagefile):
				os.makedirs("cache/" + imagefile.split("/")[0],exist_ok=True)
				with open("cache/" + imagefile,"wb") as fi:
					fi.write(data)


			if i.type == 3: artworks["album"].append(artwork)

		return artworks

	def metadata(self):
		try:
			return self.cached_metadata
		except:
			pass

		ext = self.path.split(".")[-1].lower()
		if ext in ["flac"]:
			audio = FLAC(self.path)

			tags = audio.tags
			try:
				album = [entry[1] for entry in tags if entry[0] == "ALBUM"][0]
			except:
				album = None
			try:
				title = [entry[1] for entry in tags if entry[0] == "TITLE"][0]
			except:
				title = self.path.split("/")[-1].split(".")[0]
			artists = [entry[1] for entry in tags if entry[0] == "ARTIST"]
			try:
				albumartist = [entry[1] for entry in tags if entry[0] == "ALBUMARTIST"][0]
			except:
				albumartist = None

			length = int(audio.info.length)

		elif ext in ["mp3"]:
			audio = MP3(self.path)

			tags = audio.tags
			try:
				album = tags.get("TALB").text[0]
			except:
				album = None
			try:
				title = tags.get("TIT2").text[0]
			except:
				title = self.path.split("/")[-1].split(".")[0]

			#artists = [set(obj.text) for obj in tags.getall("TPE1") + tags.getall("TPE2") + tags.getall("TPE3") + tags.getall("TPE4")]
			artists = [set(obj.text) for obj in tags.getall("TPE1")]
			artists = set.union(*artists)
			try:
				albumartist = tags.get("TPE2").text[0]
			except:
				albumartist = None

			length = int(audio.info.length)

		self.cached_metadata = {
			"title":title,
			"artists":artists,
			"album":album,
			"albumartist":albumartist,
			"length":length,

		}

		return self.cached_metadata


class Artist(db.DBObject):
	__primary__ = "name",
	name: str
	artworks: list = MultiRef(Artwork,exclusive=False,backref="artist")
	artwork_index: int

	def __apidict__(self):
		return {
			"uid":self.uid,
			"name":self.name,
			#"sorttitle":self.name.lower(),
		#	"artwork":[a.uid for a in self.artwork],
			"artwork":self.get_artwork().link(),
			"artwork_choices":[a.link() for a in self.artworks],
			"last_played":max([t.lastplayed for t in self.tracks] + [0]),
			"times_played":sum(t.timesplayed for t in self.tracks),
			"track_ids":[track.uid for track in self.tracks]
		}

	def get_artwork(self):
		if len(self.artworks) > 0: return self.artworks[self.artwork_index]
		else: return PseudoArtwork("artist")

	def get_tracklist(self):
		return self.tracks


class Album(db.DBObject):
	__primary__ = "name","albumartists"
	name: str
	albumartists: list = MultiRef(Artist,exclusive=False,backref="albums")
	artworks: list = MultiRef(Artwork,exclusive=False,backref="album")
	artwork_index: int

	def __apidict__(self):
		return {
			"uid":self.uid,
			"albumartists":[{"id":a.uid,"name":a.name} for a in self.albumartists],
		#	"albumartist_ids":list(a.uid for a in self.albumartists),
		#	"albumartist_names":list(a.name for a in self.albumartists),
			"name":self.name,
			#"sorttitle":self.name.lower(),
		#	"artwork":[a.uid for a in self.artwork],
			"artwork":self.get_artwork().link(),
			"artwork_choices":[a.link() for a in self.artworks],
			"last_played":max([t.lastplayed for t in self.tracks] + [0]),
			"times_played":sum(t.timesplayed for t in self.tracks),
			"track_ids":[track.uid for track in self.tracks]
		}

	def get_artwork(self):
		if len(self.artworks) > 0: return self.artworks[self.artwork_index]
		else: return PseudoArtwork("album")


class Track(db.DBObject):
	__primary__ = "title","artists"
	title: str
	artists: list = MultiRef(Artist,backref="tracks",exclusive=False)
	albums: list = MultiRef(Album,backref="tracks",exclusive=False)
	audiofiles: list = MultiRef(Audio,exclusive=True,backref="track")
	artworks: list = MultiRef(Artwork,exclusive=False,backref="track")
	artwork_index: int
	length: int
	lastplayed: int
	timesplayed: int

	def __apidict__(self):
		return {
			"uid":self.uid,
			"title":self.title,
			"length":self.length,
			#"sorttitle":self.title.lower(),
			"artists":[{"id":a.uid,"name":a.name} for a in self.artists],
		#	"artist_ids":list(a.uid for a in self.artists),
		#	"artist_names":list(a.name for a in self.artists),
		#	"artwork":[a.uid for a in self.artwork],
			"artwork":self.get_artwork().link(),
			"artwork_choices":[a.link() for a in self.artworks],
			"last_played":self.lastplayed,
			"times_played":self.timesplayed,
			"track_ids":[self.uid]
		}

	def get_artwork(self):
		if len(self.artworks) > 0: return self.artworks[self.artwork_index]
		else:
			for a in self.albums:
				if len(a.artworks) > 0: return a.artworks[a.artwork_index]
		return PseudoArtwork("track")

	def get_audio(self):
		if len(self.audiofiles) > 0: return self.audiofiles[0]
		return None

	def get_tracklist(self):
		return [self]





from doreah import auth

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
	result["tracks"] = list(artist.tracks)
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
	result["tracks"] = list(album.tracks)
	# sort artists by presence on this album
	artisttracks = {}
	for t in result["tracks"]:
		for a in t.artists:
			artisttracks[a] = artisttracks.setdefault(a,0) + 1
	result["artists"] = sorted([a for a in artisttracks],key=lambda x: artisttracks[x],reverse=True)
	#result["artists"] = list(set(a for t in result["tracks"] for a in t.artists))

	return result

@api.get("track/{id}")
def get_track(id:int):
	track = db.get(id)
	result = {}
	result["track"] = track
	result["artists"] = list(track.artists)
	result["albums"] = list(track.albums)

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
IMAGEFORMATS = ["jpeg","jpg","png","webp"]

from scanners.structural import build_database

def prune_database():

	# remove file references that have no objects
	artworks = db.getall(Artwork)
	referenced_artworks = set().union(*[set(entity.artworks) for entity in db.getall(Track) + db.getall(Album) + db.getall(Artist)])
	for a in artworks:
		if a not in referenced_artworks:
			print(a.path,"no longer referenced, removing...")
			db.delete(a)

	audiofiles = db.getall(Audio)
	referenced_audiofiles = set().union(*[set(entity.audiofiles) for entity in db.getall(Track)])
	for a in audiofiles:
		if a not in referenced_audiofiles:
			print(a.path,"no longer referenced, removing...")
			db.delete(a)

	# remove tracks that have no audiofiles

def save_database():
	db.save()
