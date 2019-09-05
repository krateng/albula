import pickle


db = {
	"classes":{},
	"objects":[]
}

def save_database():
	with open("database.pck","wb") as f:
		pickle.dump(db,f)


def load_database():
	global db
	try:
		with open("database.pck","rb") as f:
			dbl = pickle.load(f)
			db["classes"], db["objects"] = dbl["classes"], dbl["objects"]
	except:
		pass


class Ref:
	def __init__(self,cls,backref=None,exclusive=False):
		self.cls = cls
		self.backref = backref
		self.exclusive = exclusive

class MultiRef(Ref):
	pass

class DBObject:
	def __repr__(self):
		try:
			name = self.name
		except:
			try:
				name = self.title
			except:
				name = "Unknwon"
		return "<[" + str(self.uid) + "] " + self.__class__.__name__  + " '" + name + "'>"

	def __init_subclass__(cls):
		# register class
		db["classes"][cls] = []

		# create constructor
		types = cls.__annotations__
		def init(self,types=types,**vars):
			for v in vars:
				# set attributes according to keyword arguments
				assert isinstance(vars[v],types[v])
				setattr(self,v,vars[v])

			# set defaults
			for v in types:
				if v not in vars:
					setattr(self,v,types[v]()) # can just call type to get a version of it, e.g. list() -> []

			self.uid = len(db["objects"])
			db["objects"].append(self)
			db["classes"][cls].append(self)
		cls.__init__ = init

		# add to referenced classes
		for v in types:
			if v in cls.__dict__:
				classvar = cls.__dict__[v]
				if isinstance(classvar,Ref) and classvar.backref is not None:
					# make getter method that checks instances of THIS object for references to the target object

					# 1 to 1
					if classvar.exclusive and not isinstance(classvar,MultiRef):
						def find_object_that_references_me(self,attr=v):
							for obj in db["classes"][cls]:
								if obj.__getattribute__(attr) is self: return obj
						prop = property(find_object_that_references_me)

					# many to 1
					elif not classvar.exclusive and not isinstance(classvar,MultiRef):
						def find_objects_that_reference_me(self,attr=v):
							for obj in db["classes"][cls]:
								if obj.__getattribute__(attr) is self: yield obj
						prop = property(find_objects_that_reference_me)

					# 1 to many
					elif classvar.exclusive and isinstance(classvar,MultiRef):
						def find_object_that_references_me_among_others(self,attr=v):
							for obj in db["classes"][cls]:
								if self in obj.__getattribute__(attr): return obj
						prop = property(find_object_that_references_me_among_others)

					# many to many
					elif not classvar.exclusive and isinstance(classvar,MultiRef):
						def find_objects_that_reference_me_among_others(self,attr=v):
							for obj in db["classes"][cls]:
								if self in obj.__getattribute__(attr): yield obj
						prop = property(find_objects_that_reference_me_among_others)

					#cls.__dict__[var] = prop
					setattr(classvar.cls,classvar.backref,prop)
