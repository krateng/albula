# non-relational db

from nimrodel import EAPI
import os

import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

import cleanup

from db_oo_helper import Ref, MultiRef, DBObject


db = {
	"classes":{},
	"objects":[]
}


class Artwork(DBObject):
	path: str

class Audio(DBObject):
	path: str



class Album(DBObject):
	name: str
	albumartist: str
	artwork: list = MultiRef(Artwork,exclusive=False)

	def __apidict__(self):
		return {
			"uid":self.uid,
			"albumartist":self.albumartist,
			"name":self.name,
			"artwork":[a.uid for a in self.artwork]
		}

class Artist(DBObject):
	name: str
	artwork: list = MultiRef(Artwork,exclusive=False)

	def __apidict__(self):
		return {
			"uid":self.uid,
			"name":self.name,
			"artwork":[a.uid for a in self.artwork]
		}

class Track(DBObject):
	title: str
	artists: list = MultiRef(Artist,backref="tracks",exclusive=False)
	albums: list = MultiRef(Album,backref="tracks",exclusive=False)
	audiofiles: list
	artwork: list = MultiRef(Artwork,exclusive=False)

	def __apidict__(self):
		return {
			"uid":self.uid,
			"title":self.title,
			"artists":self.artists,
			"artwork":[a.uid for a in self.artwork]
		}



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
	return db["classes"][Artist]

@api.get("albums")
def list_albums():
	return db["classes"][Album]

@api.get("tracks")
def list_tracks():
	return db["classes"][Track]


@api.get("artist/{id}")
def get_artist(id:int):
	artist = db["objects"][id]
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
	album = db["objects"][id]
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
	path = db["objects"][uid].path
	return path



def build_database(dirs):


	scanned = 0

	pics_album = []
	pics_artist = []
	# temporary pic storage. we need to wait til we have all the music files so we can match them

	for dir in dirs:
		for (root,dirs,files) in os.walk(dir,followlinks=True):
			for f in files:
				#print("Scanning file",f)
				scanned += 1
				if scanned % 25 == 0:
					print(scanned,"files scanned...")
				fullpath = os.path.join(dir,root,f)
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
					track = add_of_find_existing_track(title=title,artists=artists,album=album,albumartist=albumartist,file=fullpath,session=session)

					if "album" in embedded_pictures:
						imghash,mime,data = embedded_pictures["album"]
						imagefile = str(imghash) + "." + mime.split("/")[-1]
						if not os.path.exists("cache/" + imagefile):
							with open("cache/" + imagefile,"wb") as fi:
								fi.write(data)
							#ref = AlbumArtRef(album_id=track.album.uid,path="cache/" + imagefile)
							track.artwork.append(Artwork(path="cache/" + imagefile))
							#print("Added embedded album art for",track)
							session.add(ref)


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
		for result in [audio for audio in db["classes"][Audio] if audio.path.startswith(imgpath):
			albums = result.track.artists
			for a in artists:
				artist_occurences[a] = artist_occurences.get(a,0) + 1

		try:
			artist = sorted([a for a in artist_occurences],key=lambda x: artist_occurences[x],reverse=True)[0]
			ref = ArtistArtRef(artist_id=artist.uid,path=img)
			session.add(ref)
		except:
			pass


		for result in session.query(FileRef).filter(FileRef.path.startswith(imgpath)):
			# if any music file is in the same folder as the image (including subfolders), associate it
			result.track.
			id = result.track.album.uid
			ref = AlbumArtRef(album_id=id,path=img)
			#print("Found",result.path)
			session.add(ref)
			break

	for img in pics_artist:
		imgpath = "/".join(img.split("/")[:-1])
		# find ALL tracks in folders and subfolders
		artist_occurences = {}
		for result in session.query(FileRef).filter(FileRef.path.startswith(imgpath)):
			artists = result.track.artists
			for a in artists:
				artist_occurences[a] = artist_occurences.get(a,0) + 1

		try:
			artist = sorted([a for a in artist_occurences],key=lambda x: artist_occurences[x],reverse=True)[0]
			ref = ArtistArtRef(artist_id=artist.uid,path=img)
			session.add(ref)
		except:
			pass


	session.commit()
