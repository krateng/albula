# non-relational db

from nimrodel import EAPI
import os
import requests

import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

import cleanup


#from db_oo_helper import Ref, MultiRef, DBObject, db, save_database, load_database
from doreah.database import Database, Ref, MultiRef
from doreah.settings import get_settings

db = Database(file="database.ddb")


class Artwork(db.DBObject):
	path: str

	def read(self):
		if self.path.endswith(".jpeg") or self.path.endswith(".jpg"):
			mime = 'image/jpeg'
		elif self.path.endswith(".png"):
			mime = 'image/png'
		with open(self.path,"rb") as imagefile:
			stream = imagefile.read()

		return mime,stream

class Audio(db.DBObject):
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


def save_database():
	db.save()

def build_database(dirs):


	scanned = 0

	pics_album = []
	pics_artist = []
	# temporary pic storage. we need to wait til we have all the music files so we can match them

	alreadydone = set(a.path for a in db.getall(Audio)).union(set(a.path for a in db.getall(Artwork)))

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

						length = int(audio.info.length)


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

						length = int(audio.info.length)


					# extract track from file and add to database
					artists,title = cleanup.fullclean(artists,title)
					track = add_of_find_existing_track(title=title,artists=artists,album=album,albumartist=albumartist,file=fullpath,length=length)

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





def add_of_find_existing_track(title,artists,album,albumartist,file,length):



	albumobj = add_of_find_existing_album(album,albumartist)
	artistobjs = [add_of_find_existing_artist(artist) for artist in artists]

	for t in db.getall(Track):
		if t.artists == artistobjs and t.title == title:
			trackobj = t
			break
	else:
		trackobj = Track(title=title,albums=[albumobj],artists=artistobjs,length=length)

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
