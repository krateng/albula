from ..db import db, Track, Album, Artist, Audio, Artwork
from doreah.io import ProgressBar

def prune_database():

	alltracks = db.getall(Track)
	allalbums = db.getall(Album)
	allartists = db.getall(Artist)

	allartworks = db.getall(Artwork)
	allaudios = db.getall(Audio)

	prog = ProgressBar(
		len(alltracks) + len(allalbums) + len(allartists) + len(allartworks) + len(allaudios),
		prefix="Pruning database    "
	)

	referenced_audiofiles = set()
	referenced_artworks = set()

	for t in alltracks:
		# remove track if it has no audio files
		if t.audiofiles == []:
			#print(t,"has no music file associated, removing...")
			db.delete(t)

		# list all refrenced files
		for af in t.audiofiles:
			referenced_audiofiles.add(af)
		for aw in t.artworks:
			referenced_artworks.add(aw)

		prog.progress()

	for e in allalbums + allartists:
		# remove album / artist if no tracks / albums
		if e.tracks == [] and getattr(e,"albums",[]) == []:
			#print(e,"has no tracks, removing...")
			db.delete(e)

		for aw in e.artworks:
			referenced_artworks.add(aw)

		prog.progress()


	for a in allartworks:
		if a not in referenced_artworks:
			#print(a.path,"no longer referenced, removing...")
			db.delete(a)
		prog.progress()
	for a in allaudios:
		if a not in referenced_audiofiles:
			#print(a.path,"no longer referenced, removing...")
			db.delete(a)
		prog.progress()

	prog.done()
