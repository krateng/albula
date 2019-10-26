from nimrodel import EAPI
from doreah import auth, settings
import hashlib
import db



def subsonicauth(request):
	print(request.url)
	for k in request.query:
		print(k, "=",request.query.get(k))
	try:
		token = request.query.get("t")
		salt = request.query.get("s")

		key = settings.get_settings("SUBSONIC_KEY")

		m = hashlib.md5()
		m.update(key.encode())
		m.update(salt.encode())

		if m.hexdigest() == token:
#			print("Success!")
			return True

		assert False
	except:
		raise
		return False



api = EAPI(path="subsonicapi/rest",delay=True,auth=subsonicauth,type="xml",root_node="subsonic-response")

base_response = {
	"xmlns":"http://subsonic.org/restapi",
	"status":"ok",
	"version":"1.13.0"
}

@api.get("ping.view")
def ping(**kwargs):
	return base_response

@api.get("getUser.view")
def getuser(**kwargs):
	return {**base_response, **{
		"user":{
			"username":"The User",
			"email":"Who knows",
			"scrobblingEnabled":"true",
			"adminRole":"false",
			"settingsRole":"false",
			"downloadRole":"true",
			"uploadRole":"false",
			"playlistRole":"false",
			"coverArtRole":"false",
			"commentRole":"false",
			"podcastRole":"false",
			"streamRole":"false",
			"jukeboxRole":"false",
			"shareRole":"false"
		}
	}}

@api.get("getRandomSongs.view")
def getrandomsongs(size:int=10,**kwargs):
	return {**base_response, **{
		"randomSongs":{
			"song":[
				{"id":t.uid,"title":t.title,"album":t.albums[0].name,"artist":", ".join(a.name for a in t.artists)}
				for t in db.db.getall(db.Track)[:size]
			]
		}
	}}

@api.get("getArtists.view")
def getartists(**kwargs):
	return {**base_response, **{
		"artists":{
			"index":[
				{"name":char,
				"artist":[
					{"id":a.uid,"name":a.name,"coverArt":a.get_artwork().uid,"albumCount":len(a.albums)}
					for a in db.db.getall(db.Artist) if a.name.startswith(char)
				]}
				for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
			]
		}
	}}

@api.get("getCoverArt.view")
def getcoverart(id:int,**kwargs):
	stream = db.db.get(id).get_artwork().read()[1]
	print(stream)
