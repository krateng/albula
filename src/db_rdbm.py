import os
from collections import namedtuple

import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

import cleanup

from db_rdbm_helper import DBClass, Session, init_database, Reference, MultiReference, meta

from sqlalchemy import create_engine, Column, Integer, String, exists, ForeignKey, Table, and_, or_
from sqlalchemy.orm import relationship, backref

from nimrodel import EAPI

# object api won't work because we don't have permanent objects (DB)
#api = OAPI(path="api")
api = EAPI(path="api",delay=True)

#class TrackArtist(DBClass):
##	__tablename__ = "trackartists"
##	uid = Column(Integer,primary_key=True,autoincrement=True)
#	track_id = Column(Integer,ForeignKey('track.uid'))
#	artist_id = Column(Integer,ForeignKey('artist.uid'))




#######
### MODELS
#######








trackartists = Table('trackartists', meta,
    Column('track_id', Integer, ForeignKey('tracks.uid')),
    Column('artist_id', Integer, ForeignKey('artists.uid'))
)

class FileRef(DBClass):
	__tablename__ = "files"
	uid = Column(Integer,primary_key=True,autoincrement=True)
	path = Column(String)
	track_id = Column(Integer,ForeignKey('tracks.uid'))

class ArtistArtRef(DBClass):
	__tablename__ = "artistart"
	uid = Column(Integer,primary_key=True,autoincrement=True)
	path = Column(String)
	artist_id = Column(Integer,ForeignKey('artists.uid'))

class AlbumArtRef(DBClass):
	__tablename__ = "albumart"
	uid = Column(Integer,primary_key=True,autoincrement=True)
	path = Column(String)
	album_id = Column(Integer,ForeignKey('albums.uid'))

class TrackArtRef(DBClass):
	__tablename__ = "trackart"
	uid = Column(Integer,primary_key=True,autoincrement=True)
	path = Column(String)
	track_id = Column(Integer,ForeignKey('tracks.uid'))


#@api.apiclass("album")
class Album(DBClass):
	__tablename__ = "albums"
	uid = Column(Integer,primary_key=True,autoincrement=True)
	name = Column(String)
	albumartist = Column(String)
	tracks = relationship("Track",backref="album",lazy=False)
	artwork = relationship(AlbumArtRef,backref="album",lazy=False)

	def __apidict__(self):
		return {
			"uid":self.uid,
			"albumartist":self.albumartist,
			"name":self.name,
			#"artwork":[a.path for a in self.artwork]
			"artwork":[a.uid for a in self.artwork]
			#"tracks":self.tracks
		}

	def __repr__(self):
		return "<Album '" + self.name + "'>"

	def get_artwork(self):
		try:
			return "/img/albumart/" + str(self.artwork[0].uid)
		except:
			return None


#@api.apiclass("artist")
class Artist(DBClass):
	__tablename__ = "artists"
	uid = Column(Integer,primary_key=True,autoincrement=True)
	name = Column(String)
	artwork = relationship(ArtistArtRef,backref="artist",lazy=False)
#	tracks = relationship(TrackArtist, backref = 'artist',lazy=False,cascade="all")

	def __apidict__(self):
		return {
			"uid":self.uid,
			"name":self.name,
			#"artwork":[a.path for a in self.artwork]
			"artwork":[a.uid for a in self.artwork]
			#"tracks":self.tracks
		}

	def __repr__(self):
		return "<Artist '" + self.name + "'>"

	def get_artwork(self):
		try:
			return "/img/artistart/" + str(self.artwork[0].uid)
		except:
			return None


#@api.apiclass("track")
class Track(DBClass):
	__tablename__ = "tracks"
	uid = Column(Integer,primary_key=True,autoincrement=True)
	title = Column(String)
#	album_id = Column(Integer,ForeignKey('album.uid'))
#	album = Reference(Album,backref="tracks")
	#artists = MultiReference(Artist,backref="tracks")

	album_id = Column(Integer,ForeignKey('albums.uid'))
	artists = relationship(Artist, secondary=lambda: trackartists, backref="tracks",lazy=False)
	files = relationship(FileRef,backref="track",lazy=False)
	artwork = relationship(TrackArtRef,backref="track",lazy=False)
#	artists = relationship(TrackArtist, backref = 'track',lazy=False,cascade="all")


	def __apidict__(self):
		return {
			"uid":self.uid,
			"title":self.title,
			"artists":self.artists,
			#"artwork":[a.path for a in self.artwork]
			"artwork":[a.uid for a in self.artwork]
		}

	def __repr__(self):
		return "<Track '" + self.title + "'>"

	def get_artwork(self):
		try:
			return "/img/trackart/" + str(self.artwork[0].uid)
		except:
			try:
				return "/img/albumart/" + str(self.album.artwork[0].uid)
			except:
				return None



init_database()








#######
### DB ACCESS FUNCTIONS
#######





def db(func):
	def wrapper(*args,**kwargs):
		if "session" in kwargs:
			session = kwargs.pop("session")
			inherited_session = True
		else:
			session = Session()
			inherited_session = False

		result = func(*args,**kwargs,session=session)

		if not inherited_session:
			session.close()

		return result

	return wrapper


@api.get("artists")
@db
def list_artists(session):
	return list(session.query(Artist))

@api.get("albums")
@db
def list_albums(session):
	return list(session.query(Album))

@api.get("tracks")
@db
def list_tracks(session):
	return list(session.query(Track))


@api.get("artist/{id}")
@db
def get_artist(id,session):
	artist = list(session.query(Artist).filter(Artist.uid == id))[0]
	result = {}
	result["artist"] = artist
	alltracks = list_tracks()
	result["tracks"] = [t for t in alltracks if artist.uid in [a.uid for a in t.artists]]
	result["albums"] = list(set(t.album for t in result["tracks"]))

	return result


@api.get("album/{id}")
@db
def get_album(id,session):
	album = list(session.query(Album).filter(Album.uid == id))[0]
	result = {}
	result["album"] = album
	alltracks = list_tracks()
	result["tracks"] = album.tracks
	# sort artists by presence on this album
	artisttracks = {}
	for t in result["tracks"]:
		for a in t.artists:
			artisttracks[a] = artisttracks.setdefault(a,0) + 1
	result["artists"] = sorted([a for a in artisttracks],key=lambda x: artisttracks[x],reverse=True)
	#result["artists"] = list(set(a for t in result["tracks"] for a in t.artists))

	return result


@db
def get_file_by_ref(uid,type,session):
	#print("getting file path for uid",uid)
	if type == "albumart":
		path = list(session.query(AlbumArtRef).filter(AlbumArtRef.uid == uid))[0].path
	elif type == "artistart":
		path = list(session.query(ArtistArtRef).filter(ArtistArtRef.uid == uid))[0].path
	elif type == "trackart":
		path = list(session.query(TrackArtRef).filter(TrackArtRef.uid == uid))[0].path
	elif type == "music":
		path = list(session.query(FileRef).filter(FileRef.uid == uid))[0].path

	return path


#Track = namedtuple("Track",["artists","title","files"])
#Album = namedtuple("Album",["albumartist","title","tracklist"])
#Artist = namedtuple("Artist",["name"])

# these are used as the keys (only unique information)
#TrackKey = namedtuple("Track",["artists","title"])
#AlbumKey = namedtuple("Album",["albumartist","title"])
#ArtistKey = namedtuple("Artist",["name"])


# we use dicts here so we can actually retrieve references to the objects when we find they are present
# python is really weird with checking whether an object is in a set, it can check if an equivalent object is there, but not return the actual object
# also this way we can have non-identifying information (like the tracklist for an album)
#ARTISTS = {}
#TRACKS = {}
#ALBUMS = {}

# REDUNDANT INFORMATION FOR PERFORMANCE
#TRACKS_OF_ARTIST = {}
#ALBUMS_OF_ARTIST = {}


def tuple_to_dict(tup):
		if isinstance(tup,Track):
			return {"artists":[tuple_to_dict(a) for a in tup.artists],"title":tup.title}
		elif isinstance(tup,Artist):
			#return {"name":tup.name}
			return tup.name
		elif isinstance(tup,Album):
			#return {"albumartist":tup.albumartist,"title":tup.title,"tracks":[tuple_to_dict(t) for t in tup.tracklist]}
			return {"albumartist":tuple_to_dict(tup.albumartist),"title":tup.title,"tracks":[tuple_to_dict(t) for t in tup.tracklist]}




#######
### BUILD
#######





def build_database(dirs):

	session = Session()
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
							ref = AlbumArtRef(album_id=track.album.uid,path="cache/" + imagefile)
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
		for result in session.query(FileRef).filter(FileRef.path.startswith(imgpath)):
			# if any music file is in the same folder as the image (including subfolders), associate it
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





def add_of_find_existing_track(title,artists,album,albumartist,file,session):



	albumobj = add_of_find_existing_album(album,albumartist,session)
	artistobjs = [add_of_find_existing_artist(artist,session) for artist in artists]

	fileref = FileRef(path=file)


	for result in session.query(Track).filter(Track.title.ilike(title)):
		if (result.artists == artistobjs and result.album == albumobj): #check same album for now, rethink pls
			trackobj = result # if there is any result, take it
			print(trackobj,"has multiple files!")
			break
	else:
		trackobj = Track(title=title,album=albumobj,artists=artistobjs)

	trackobj.files.append(fileref)

	#for a in artistobjs:
	#	TrackArtist(artist=a,track=trackobj)

	session.add(trackobj)
	session.add(fileref)
	return trackobj

def add_of_find_existing_album(name,artist,session):

	for result in session.query(Album).filter(and_(Album.name.ilike(name),Album.albumartist.ilike(artist))):
		return result

	albumobj = Album(name=name,albumartist=artist)
	session.add(albumobj)
	return albumobj

def add_of_find_existing_artist(name,session):

	for result in session.query(Artist).filter(Artist.name.ilike(name)):
		return result

	artistobj = Artist(name=name)
	session.add(artistobj)
	return artistobj









#	artistlist = []
#	for a in artists:
#		A = Artist(name=a)
#		A_ = ArtistKey(name=a)
#		if A_ not in ARTISTS:
#			ARTISTS[A_] = A
#			ALBUMS_OF_ARTIST.setdefault(A_,[]) #any artist that is newly added (via track) should go in the album artist list
#		else:
#			A = ARTISTS[A_]
#		# this is, without a doubt, the weirdest four lines i have ever written
#		artistlist.append(A)
#
#
#	ALIST = frozenset(artistlist)
#
#	T = Track(artists=ALIST,title=title,files=[file])
#	T_ = TrackKey(artists=ALIST,title=title)
#	if T_ not in TRACKS:
#		TRACKS[T_] = T
#	else:
#		T = TRACKS[T_]
#		T.files.append(file)
#
#	for A in ALIST:
#		A_ = ArtistKey(name=A.name)
#		TRACKS_OF_ARTIST.setdefault(A_,[]).append(T)
#
#	if albumartist in ["Various","Various Artists"]:
#		AA = None
#		AA_ = None
#	else:
#		AA = Artist(name=albumartist)
#		AA_ = ArtistKey(name=albumartist)
#		if AA_ not in ARTISTS:
#			ARTISTS[AA_] = AA
#			TRACKS_OF_ARTIST.setdefault(AA_,[]) # any artist defined as album artist also goes in track artist list
#		else:
#			AA = ARTISTS[AA_]
#
#	AB = Album(albumartist=AA,title=album,tracklist=[T])
#	AB_ = AlbumKey(albumartist=AA,title=album)
#
#
#	if AB_ not in ALBUMS:
#		ALBUMS[AB_] = AB
#		ALBUMS_OF_ARTIST.setdefault(AA_,[]).append(AB)
#	else:
#		AB = ALBUMS[AB_]
#		if T not in AB.tracklist:
#			AB.tracklist.append(T)






#def listartists():
#	return [tuple_to_dict(ARTISTS[A]) for A in ARTISTS]
#
#def listtracks(artist=None):
#	if artist is None:
#		return [tuple_to_dict(TRACKS[T]) for T in TRACKS]
#	else:
#		A_ = ArtistKey(name=artist)
#		return [tuple_to_dict(T) for T in TRACKS_OF_ARTIST[A_]]
#
#def listalbums(artist=None):
#	if artist is None:
#		return [tuple_to_dict(ALBUMS[AB]) for AB in ALBUMS]
#	else:
#		A_ = ArtistKey(name=artist)
#		# implement this with actual album artist references
#		return [tuple_to_dict(AB) for AB in ALBUMS_OF_ARTIST[A_]]
#
