from doreah.settings import get_settings
from doreah.io import print_progress_bar
import requests
import urllib




def get_scrobbles(tracks):

	tracks = {(frozenset(a.name.lower() for a in t.artists),t.title.lower()):t for t in tracks}
	matched_tracks = {}

	malserver = get_settings("MALOJA_SERVER")
	if malserver is None:
		malserver = input("Please enter the URL of your Maloja server: ")

	# list of tracks
	url = malserver + "/api/tracks"
	result = requests.get(url)
	result = result.json()["list"]
	for r in result:
		tr = (frozenset(a.lower() for a in r["artists"]),r["title"].lower())
		if tr in tracks:
			matched_tracks[tracks[tr]] = r

	#print(matched_tracks)


	url = malserver + "/api/trackinfo"
	i = 0
	tracknumber = len(matched_tracks)
	for t in matched_tracks:
		i += 1
		trackinfo = matched_tracks[t]
		info = []
		for a in trackinfo["artists"]: info.append(("artist",a))
		info.append(("title",trackinfo["title"]))
	#	trackurl = url + "?" + "&".join(["artist=" + a for a in trackinfo["artists"]]) + "&title=" + trackinfo["title"]
		trackurl = url + "?" + urllib.parse.urlencode(info)
	#	print("Making request",trackurl)
		result = requests.get(trackurl)
		result = result.json()
		#print(t,"has",result["scrobbles"],"scrobbles")
		print_progress_bar(num=(i,tracknumber),prefix="Importing scrobbles ")
		t.timesplayed = result["scrobbles"]

	
