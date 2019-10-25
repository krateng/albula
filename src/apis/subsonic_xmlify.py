from bottle import Response

# https://gist.github.com/reimund/5435343/
def dict2xml(d, root_node="subsonic-response"):
	wrap          =     False if None == root_node or isinstance(d, list) else True
	root          = 'objects' if None == root_node else root_node
	root_singular = root[:-1] if 's' == root[-1] and None == root_node else root
	xml           = ''
	children      = []

	if isinstance(d, dict):
		for key, value in dict.items(d):
			if isinstance(value, dict):
				children.append(dict2xml(value, key))
			elif isinstance(value, list):
				children.append(dict2xml(value, key))
			else:
				xml = xml + ' ' + key + '="' + str(value) + '"'
	else:
		for value in d:
			children.append(dict2xml(value, root_singular))

	#end_tag = '>' if 0 < len(children) else '/>'
	end_tag = '>'

	if wrap or isinstance(d, dict):
		xml = '<' + root + xml + end_tag

	if 0 < len(children):
		for child in children:
			xml = xml + child

	if wrap or isinstance(d, dict):
		xml = xml + '</' + root + '>'

	return xml


def xmlify(func):
	def newfunc(*args,**kwargs):
		result = func(*args,**kwargs)
		xml = dict2xml(result)
		return xml
	#	r = Response()
	#	r.set_header("Content-type","text/plain; charset=utf-8")
	#	r.set_header("Content-length",str(len(xml)))
	#	r.body = xml
	#	return r

	return newfunc
