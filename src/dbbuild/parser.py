# scanner that takes folder structure into account

from db import db,Audio,Artwork,Album,Artist,Track

import os
import cleanup
import yaml
#from doreah.settings import get_settings
#from doreah.io import NestedProgressBar


def scan_tree(d,prog):
	subdirs,audiofiles,imagefiles = d.subdirs, d.audiofiles, d.imagefiles


	tracks_in_folder = []
	for sd in subdirs:
		tracks_in_folder += scan_tree(sd,prog)



	# read newly scanned files
	for af in audiofiles:

		prog.progress()

		trackinfo = {}

		if af.track is None:
			metadata = af.metadata()
			artists,title = cleanup.fullclean(metadata["artists"],metadata["title"])
			albumartists,album = cleanup.cleanartists([metadata["albumartist"]]),metadata["album"]
			pos,dur = metadata["position"],metadata["length"]
			tr = Track(
				title=title,
				artists=[Artist(name=a) for a in artists],
				length=dur
			)
			tr.audiofiles.append(af)


			al = Album(
				name=album,
				albumartists=[Artist(name=a) for a in albumartists]
			)

			trackinfo["track"] = tr
			trackinfo["album"] = al
			trackinfo["position"] = pos


			#al.tracks_preliminary = getattr(album,"tracks_preliminary",[]) + [(pos,tr)]
			#al.tracks = getattr(album,"tracks",[]) + [tr]

		else:
			#print(af.path,"already has track",af.track,"with albums",af.track.albums)
			al = af.track.albums[0]
			pos = af.metadata()["position"]

			trackinfo["track"] = af.track
			trackinfo["album"] = al
			trackinfo["position"] = pos

			#al.tracks_preliminary = getattr(album,"tracks_preliminary",[]) + [(pos,tr)]


		tracks_in_folder.append(trackinfo)

	# look at all files in this subtree and check if they seem to have an album or an
	# artist in common
	albums = {}
	artists = {}
	albumartists = {}
	for trackinfo in tracks_in_folder:
		albums[trackinfo["album"]] = albums.setdefault(trackinfo["album"],0) + 1
		for artist in trackinfo["album"].albumartists:
			albumartists[artist] = albumartists.setdefault(artist,0) + 1
			artists[artist] = artists.setdefault(artist,0) # set to 0 so it's there
		for artist in trackinfo["track"].artists:
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
	if d.artist is None:
		if len(artistlist) > 0 and artists[artistlist[0]]+albumartists[artistlist[0]] >= len(tracks_in_folder)/1.5:
			d.artist = artistlist[0]
			#folder_artist = artistlist[0]


	if d.album is None:
		if len(albumlist) > 0 and albums[albumlist[0]] >= len(tracks_in_folder)/1.5:
			#print("common album",commonalbum)
			d.album = albumlist[0]
			if d.album.albumartists in [[],"",None]:
				# if most files have no album artist metadata, guess from tracks
				artists = {}
				count = 0
				#print(list(aud["albumartist"] for aud in audiofiles))
				for trackinfo in tracks_in_folder:
					if trackinfo["album"] is d.album:
						count += 1
						for a in trackinfo["track"].artists:
							artists[a] = artists.setdefault(a,0) + 1
				commonartists = []
				#print("artists",artists)
				artists_in_album = [a for a in artists]
		#		artists_in_album.sort(key=lambda x:artists[x],reverse=True)
				commonartists = [a for a in artists_in_album if artists[a] > count/2]
				if len(commonartists) == 0:
					commonartists = [Artist(name="Various Artists")]
				d.album = Album(albumartists=commonartists,name=d.album.name)

				# apply to all
			#	for tr in tracks:
			#		if tr.albums[0] is Album(albumartists=[],name=d.album.name):
			#			tr.albums = [d.album]



	# go through tracks with missing data. assign folder album / artist
	for tr in tracks_in_folder:

		#print(tr)


		if d.album is not None and tr.get("album") is None:
			tr["album"] = d.album
		elif d.album is not None and tr.get("album") is Album(albumartists=[],name=d.album.name):
			tr["album"] = d.album

		if d.artist is not None and tr["track"].artists == []:
			tr["track"].artists = [d.artist]



	## check artwork files

	for i in imagefiles:
		if "artist" in i.path.lower() and d.artist is not None and i not in d.artist.artworks:
			d.artist.artworks.append(i)
		elif "album" in i.path.lower() and d.album is not None and i not in d.album.artworks:
 			d.album.artworks.append(i)


	return tracks_in_folder





def parse(dirs,prog_parse,prog_build):

	tracks = []

	for dir in dirs:
		tracks += scan_tree(dir,prog_parse)

	prog_parse.done()


	for info in tracks:
		al = info["album"]
		pos,tr = info["position"],info["track"]
		al.tracks_preliminary = getattr(al,"tracks_preliminary",[]) + [(pos,tr)]


	# finalize album track lists
	for al in db.getall(Album):
		try:
			al.tracks = [e[1] for e in sorted(al.tracks_preliminary,key=lambda x:x[0])]
			del al.tracks_preliminary
		except:
			pass


	# all albums that have no albumartist yet get their artists as albumartist
	# all tracks that have no album get their own title as album
	for t in db.getall(Track):
		if t.albums == []:
			al = Album(name=t.title,albumartists=t.artists)
			al.tracks = [t]
	for al in db.getall(Album):
		if al.albumartists == []:
		#	al.albumartists = [ar for (p,t) in al.tracks_preliminary for ar in t.artists]
			al.albumartists = list(set([ar for t in al.tracks for ar in t.artists]))



	for aud in db.getall(Audio):
		for aw in aud.get_embedded_artworks()["album"]:
			if aw not in aud.track.albums[0].artworks:
					aud.track.albums[0].artworks.append(aw)

		prog_build.progress()

	prog_build.done()
