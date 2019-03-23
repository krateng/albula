import os
from collections import namedtuple

import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

import cleanup





Track = namedtuple("Track",["artists","title","files"])
Album = namedtuple("Album",["albumartist","title","tracklist"])
Artist = namedtuple("Artist",["name"])

# these are used as the keys (only unique information)
TrackKey = namedtuple("Track",["artists","title"])
AlbumKey = namedtuple("Album",["albumartist","title"])
ArtistKey = namedtuple("Artist",["name"])


# we use dicts here so we can actually retrieve references to the objects when we find they are present
# python is really weird with checking whether an object is in a set, it can check if an equivalent object is there, but not return the actual object
# also this way we can have non-identifying information (like the tracklist for an album)
ARTISTS = {}
TRACKS = {}
ALBUMS = {}

# REDUNDANT INFORMATION FOR PERFORMANCE
TRACKS_OF_ARTIST = {}
ALBUMS_OF_ARTIST = {}


def tuple_to_dict(tup):
        if isinstance(tup,Track):
            return {"artists":[tuple_to_dict(a) for a in tup.artists],"title":tup.title}
        elif isinstance(tup,Artist):
            #return {"name":tup.name}
            return tup.name
        elif isinstance(tup,Album):
            #return {"albumartist":tup.albumartist,"title":tup.title,"tracks":[tuple_to_dict(t) for t in tup.tracklist]}
            return {"albumartist":tuple_to_dict(tup.albumartist),"title":tup.title,"tracks":[tuple_to_dict(t) for t in tup.tracklist]}

def build_database(dir):
    for (root,dirs,files) in os.walk(dir,followlinks=True):
        for f in files:
            fullpath = os.path.join(dir,root,f)

            if f.endswith(".flac"):
                audio = FLAC(fullpath)

                tags = audio.tags
                album = [entry[1] for entry in tags if entry[0] == "ALBUM"][0]
                title = [entry[1] for entry in tags if entry[0] == "TITLE"][0]
                artists = [entry[1] for entry in tags if entry[0] == "ARTIST"]
                try:
                    albumartist = [entry[1] for entry in tags if entry[0] == "ALBUMARTIST"][0]
                except:
                    albumartist = ", ".join(artists)

            elif f.endswith(".mp3"):
                audio = MP3(fullpath)

                tags = audio.tags
                album = tags.get("TALB").text[0]
                title = tags.get("TIT2").text[0]
                #artists = [set(obj.text) for obj in tags.getall("TPE1") + tags.getall("TPE2") + tags.getall("TPE3") + tags.getall("TPE4")]
                artists = [set(obj.text) for obj in tags.getall("TPE1")]
                artists = set.union(*artists)
                try:
                    albumartist = tags.get("TPE2").text[0]
                except:
                    albumartist = ", ".join(artists)

            else:
                continue





            add_track(title=title,artists=artists,album=album,albumartist=albumartist,file=fullpath)


def add_track(title,artists,album,albumartist,file):

    artists,title = cleanup.fullclean(artists,title)

    artistlist = []
    for a in artists:
        A = Artist(name=a)
        A_ = ArtistKey(name=a)
        if A_ not in ARTISTS:
            ARTISTS[A_] = A
            ALBUMS_OF_ARTIST.setdefault(A_,[]) #any artist that is newly added (via track) should go in the album artist list
        else:
            A = ARTISTS[A_]
        # this is, without a doubt, the weirdest four lines i have ever written
        artistlist.append(A)


    ALIST = frozenset(artistlist)

    T = Track(artists=ALIST,title=title,files=[file])
    T_ = TrackKey(artists=ALIST,title=title)
    if T_ not in TRACKS:
        TRACKS[T_] = T
    else:
        T = TRACKS[T_]
        T.files.append(file)

    for A in ALIST:
        A_ = ArtistKey(name=A.name)
        TRACKS_OF_ARTIST.setdefault(A_,[]).append(T)

    if albumartist in ["Various","Various Artists"]:
        AA = None
        AA_ = None
    else:
        AA = Artist(name=albumartist)
        AA_ = ArtistKey(name=albumartist)
        if AA_ not in ARTISTS:
            ARTISTS[AA_] = AA
            TRACKS_OF_ARTIST.setdefault(AA_,[]) # any artist defined as album artist also goes in track artist list
        else:
            AA = ARTISTS[AA_]

    AB = Album(albumartist=AA,title=album,tracklist=[T])
    AB_ = AlbumKey(albumartist=AA,title=album)


    if AB_ not in ALBUMS:
        ALBUMS[AB_] = AB
        ALBUMS_OF_ARTIST.setdefault(AA_,[]).append(AB)
    else:
        AB = ALBUMS[AB_]
        if T not in AB.tracklist:
            AB.tracklist.append(T)






def listartists():
    return [tuple_to_dict(ARTISTS[A]) for A in ARTISTS]

def listtracks(artist=None):
    if artist is None:
        return [tuple_to_dict(TRACKS[T]) for T in TRACKS]
    else:
        A_ = ArtistKey(name=artist)
        return [tuple_to_dict(T) for T in TRACKS_OF_ARTIST[A_]]

def listalbums(artist=None):
    if artist is None:
        return [tuple_to_dict(ALBUMS[AB]) for AB in ALBUMS]
    else:
        A_ = ArtistKey(name=artist)
        # implement this with actual album artist references
        return [tuple_to_dict(AB) for AB in ALBUMS_OF_ARTIST[A_]]
