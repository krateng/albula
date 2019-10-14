# scanner that takes folder structure into account

from db import db,Audio,Artwork,Album,Artist,Track

from doreah.io import NestedProgressBar, ProgressBar

import os
import cleanup
import yaml
#from doreah.settings import get_settings
#from doreah.io import NestedProgressBar



def build_metadata(filelist,trees):

	prog_build = ProgressBar(
		len(filelist),
		prefix="Parsing metadata    "
	)

	todo = []
	if len(filelist) > 0:
		for t in trees:
			td, _ = scan_tree_for(filelist,t,prog_build)
			todo += td



	for af in todo:
		if af.track.artists == []:
			af.track.artists = [Artist("Various Artists")]
		if af.track.albums == []:
			Album(albumartists=af.track.artists,name=af.track.title).tracks.append(af.track)
		prog_build.progress(step=af.track.title)

	prog_build.done()

	for alb in db.getall(Album):
		if alb.albumartists == []:
			artists = {}
			for t in alb.tracks:
				for a in t.artists:
					artists[a] = artists.setdefault(a,0) + 1
			artists_in_album = [a for a in artists]
	#		artists_in_album.sort(key=lambda x:artists[x],reverse=True)
			commonartists = [a for a in artists_in_album if artists[a] > len(alb.tracks)/2]
			if len(commonartists) == 0:
				commonartists = [Artist(name="Various Artists")]
			albnew = Album(albumartists=commonartists,name=alb.name)
			albnew.artworks = alb.artworks

			for t in alb.tracks:
			 	albnew.tracks.append(t)
			db.delete(alb)



	prog_imag = ProgressBar(
		len(filelist),
		prefix="Extracting artwork  "
	)


	for aud in filelist:
		prog_imag.progress()
		for aw in aud.get_embedded_artworks()["album"]:
			if aw not in aud.track.albums[0].artworks:
					aud.track.albums[0].artworks.append(aw)



	newly_created_tracks = [f.track for f in filelist]
	affected_albums = list(set([t.albums[0] for t in newly_created_tracks]))

	prog_alb = ProgressBar(
		len(affected_albums),
		prefix="Fixing album orders "
	)

	for alb in affected_albums:
		tracks = alb.tracks
		numstracks = [(t.audiofiles[0].metadata()["position"],t) for t in tracks]
		numstracks.sort(key=lambda x:x[0])
		alb.tracks = [nt[1] for nt in numstracks]
		prog_alb.progress()


def scan_tree_for(files,tree,progressbar):
	subdirs,audiofiles,imagefiles = tree.subdirs, tree.audiofiles, tree.imagefiles

	# sort into ones we can use to gather info about the folder
	# and the ones we want to find out metadata about
	todo_audiofiles, scanned_audiofiles = [],[]
	for sd in subdirs:
		td,sc = scan_tree_for(files,sd,progressbar)
		todo_audiofiles += td
		scanned_audiofiles += sc


	for af in audiofiles:
		if af in files: todo_audiofiles.append(af)
		elif af.track: scanned_audiofiles.append(af)
		else: print(af,"has no track, but will not be scanned!")



	possible_folder_artists = {}
	possible_folder_albums = {}
	possible_folder_albumartists = {}


	# check if we even need to find out anything about this folder
	if tree.artist is None or tree.album is None:

		for af in scanned_audiofiles:
			track = af.track
			album = track.albums[0]
			artists = track.artists
			albumartists = album.albumartists

			pos = af.metadata()["position"]

			possible_folder_albums[album] = possible_folder_albums.setdefault(album,0) + 1
			for artist in albumartists:
				possible_folder_albumartists[artist] = possible_folder_albumartists.setdefault(artist,0) + 1
				possible_folder_artists[artist] = possible_folder_artists.setdefault(artist,0) # set to 0 so it's there
			for artist in artists:
				possible_folder_artists[artist] = possible_folder_artists.setdefault(artist,0) + 1
				possible_folder_albumartists[artist] = possible_folder_albumartists.setdefault(artist,0) # set to 0 so it's there




	# scan the files
	for af in todo_audiofiles[:]:
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



		if tree.artist is None or tree.album is None:
			for artist in tr.artists:
				possible_folder_artists[artist] = possible_folder_artists.setdefault(artist,0) + 1
				possible_folder_albumartists[artist] = possible_folder_albumartists.setdefault(artist,0)

		if album not in [None,""]:

			al = Album(
				name=album,
				albumartists=[Artist(name=a) for a in albumartists]
			)
			al.tracks.append(tr)

			if tree.artist is None or tree.album is None:
				for artist in al.albumartists:
					possible_folder_albumartists[artist] = possible_folder_albumartists.setdefault(artist,0) + 1
					possible_folder_artists[artist] = possible_folder_artists.setdefault(artist,0)
				possible_folder_albums[al] = possible_folder_albums.setdefault(al,0) + 1

			if albumartists != [] and artists != []:
				# metadata fully parsed from embedded data, we're good!
				progressbar.progress(step=af.path)
				scanned_audiofiles.append(af)
				todo_audiofiles.remove(af)
				# this also means this will below be counted to find out folder album / artist
				continue



	total_files = len(todo_audiofiles) + len(scanned_audiofiles)

	# if not, now try to determine folder album / artist
	if tree.artist is None:
		artistlist = list(set(a for a in possible_folder_artists))
		artistlist.sort(key=lambda x:possible_folder_artists[x]+possible_folder_albumartists[x],reverse=True)
		if len(artistlist) > 0 and possible_folder_artists[artistlist[0]]+possible_folder_albumartists[artistlist[0]] >= total_files/1.5:
			tree.artist = artistlist[0]

	if tree.album is None:
		albumlist = [a for a in possible_folder_albums]
		albumlist.sort(key=lambda x:possible_folder_albums[x],reverse=True)
		if len(albumlist) > 0 and possible_folder_albums[albumlist[0]] >= total_files/1.5:
			#print("common album",commonalbum)
			tree.album = albumlist[0]
			if tree.album.albumartists in [[],"",None]:
				if tree.artist is not None:
					tree.album.albumartists = [tree.artist]
					# set folder artist as albumartist




	# assign folder album / artist to tracks that are still missing it
	for af in todo_audiofiles[:]:
		if af.track.artists == [] and tree.artist is not None:
			af.track.artists = [tree.artist]
		if af.track.albums == [] and tree.album is not None:
			tree.album.tracks.append(af.track)

		if af.track.artists != [] and af.track.albums != []:
			progressbar.progress(step=af.path)
			scanned_audiofiles.append(af)
			todo_audiofiles.remove(af)

		if af.track.albums != [] and af.track.albums[0].albumartists == [] and \
				tree.album is not None and af.track.albums[0].name == tree.album.name:
			af.track.albums[0].tracks.remove(af.track)
			tree.album.tracks.append(af.track)


		if af.track.albums != [] and af.track.albums[0].albumartists == [] and tree.artist is not None:
			af.track.albums[0].albumartists = [tree.artist]



	## check artwork files
	for i in imagefiles:
		if "artist" in i.path.lower() and tree.artist is not None and i not in tree.artist.artworks:
			tree.artist.artworks.append(i)
		elif "album" in i.path.lower() and tree.album is not None and i not in tree.album.artworks:
 			tree.album.artworks.append(i)


	return todo_audiofiles, scanned_audiofiles
