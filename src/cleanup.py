import re
import unicodedata
from doreah.settings import get_settings
import yaml
import os

def fullclean(artists_,title):
	artists = []
	for a in artists_:
		artists += parseArtists(removespecial(a))
	#artists = parseArtists(removespecial(artist))
	title = parseTitle(removespecial(title))
	(title,moreartists) = parseTitleForArtists(title)
	artists += moreartists
	artists = list(set(artists))
	artists.sort()

	return (artists,title)

def cleanartists(artists_):
	artists = []
	for a in artists_:
		artists += parseArtists(removespecial(a))
	artists = list(set(artists))
	artists.sort()
	return artists

def removespecial(s):
	s = s.replace("\t","").replace("␟","").replace("\n","")
	s = re.sub(" +"," ",s)
	return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")



delimiters_feat = ["ft.","ft","feat.","feat","featuring","Ft.","Ft","Feat.","Feat","Featuring"]			#Delimiters used for extra artists, even when in the title field
delimiters = ["vs.","vs","&"]											#Delimiters in informal artist strings, spaces expected around them.
delimiters = get_settings("ARTIST_DELIMITERS")							#risk of false positives. user has control over tagging
delimiters_formal = ["; ",";","/"]										#Delimiters used specifically to tag multiple artists when only one tag field is available, no spaces used

safe_artists = []
for f in os.listdir("rules"):
	if not f.startswith("."):
		with open("rules/" + f,"r") as fil:
			d = yaml.safe_load(fil)
			safe_artists += d["artists"]

def parseArtists(a):

	if a.strip() == "":
		return []

#		if a.strip() in rules_notanartist:
#			return []

	if " performing " in a.lower():
		return parseArtists(re.split(" [Pp]erforming",a)[0])

	if a.strip() in safe_artists:
		return [a.strip()]
#		if a.strip() in rules_replaceartist:
#			return rules_replaceartist[a.strip()].split("␟")



	for d in delimiters_feat:
		if re.match(r"(.*) \(" + d + " (.*)\)",a) is not None:
			return parseArtists(re.sub(r"(.*) \(" + d + " (.*)\)",r"\1",a)) + parseArtists(re.sub(r"(.*) \(" + d + " (.*)\)",r"\2",a))

	for d in delimiters_formal:
		if (d in a):
			ls = []
			for i in a.split(d):
				ls += parseArtists(i)
			return ls

	for d in (delimiters_feat + delimiters):
		if ((" " + d + " ") in a):
			ls = []
			for i in a.split(" " + d + " "):
				ls += parseArtists(i)
			return ls





	return [a.strip()]

def parseTitle(t):
#		if t.strip() in rules_replacetitle:
#			return rules_replacetitle[t.strip()]

	t = t.replace("[","(").replace("]",")")

	t = re.sub(r" \(as made famous by .*?\)","",t)
	t = re.sub(r" \(originally by .*?\)","",t)
	t = re.sub(r" \(.*?Remaster.*?\)","",t)

	return t.strip()

def parseTitleForArtists(t):
	for d in delimiters_feat:
		if re.match(r"(.*) \(" + d + " (.*?)\)",t) is not None:
			(title,artists) = parseTitleForArtists(re.sub(r"(.*) \(" + d + " (.*?)\)",r"\1",t))
			artists += parseArtists(re.sub(r"(.*) \(" + d + " (.*?)\).*",r"\2",t))
			return (title,artists)
		if re.match(r"(.*) - " + d + " (.*)",t) is not None:
			(title,artists) = parseTitleForArtists(re.sub(r"(.*) - " + d + " (.*)",r"\1",t))
			artists += parseArtists(re.sub(r"(.*) - " + d + " (.*).*",r"\2",t))
			return (title,artists)
		if re.match(r"(.*) " + d + " (.*)",t) is not None:
			(title,artists) = parseTitleForArtists(re.sub(r"(.*) " + d + " (.*)",r"\1",t))
			artists += parseArtists(re.sub(r"(.*) " + d + " (.*).*",r"\2",t))
			return (title,artists)

	return (t,[])
