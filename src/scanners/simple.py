# scanner that looks at individual files and their metadata

from db import db,Audio,Artwork,Album,Artist,Track,AUDIOFORMATS,IMAGEFORMATS

import os
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import zlib

import cleanup

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
								embedded_pictures["album"] = (zlib.adler32(i.data),i.mime,i.data)



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
								embedded_pictures["album"] = (zlib.adler32(i.data),i.mime,i.data)


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

					track = Track(
						title=title,
						albums=[Album(name=album,albumartist=albumartist)],
						artists=[Artist(name=name) for name in artists],
						length=length
					)

					track.audiofiles.append(Audio(path=fullpath))

					if "album" in embedded_pictures:
						imghash,mime,data = embedded_pictures["album"]
						hsh = str(imghash)

						imagefile = hsh[:3] + "/" + hsh[3:] + "." + mime.split("/")[-1]
						if not os.path.exists("cache/" + imagefile):
							os.makedirs("cache/" + imagefile.split("/")[0],exist_ok=True)
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
