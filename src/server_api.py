from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template
import waitress

import db


apiserver = Bottle()


@apiserver.get("/listartists")
def listartists():
        return {"artists":db.listartists()}

@apiserver.get("/listtracks")
def listtracks():
        keys = FormsDict.decode(request.query)
        return {"tracks":db.listtracks(artist=keys.get("artist"))}

@apiserver.get("/listalbums")
def listalbums():
        keys = FormsDict.decode(request.query)
        if keys.get("artist") is None:
            return {"albums":db.listalbums(artist=keys.get("artist"))}
        else:
            tracks = db.listtracks(artist=keys.get("artist"))
            allalbums = db.listalbums()
            albums = []
            for album in allalbums:
                appear = False
                for track in album["tracks"]:
                    if keys.get("artist") in track["artists"]: appear = True
                if appear: albums.append(album)

            return {"albums":db.listalbums(artist=keys.get("artist")),"appearing":albums}




def runserver(port):
    run(apiserver, host='::', port=port, server='waitress')
