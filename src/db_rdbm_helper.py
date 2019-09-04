# some personal adjustments to SQLAlchemy

from sqlalchemy import create_engine, Column, Integer, String, exists, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

VERBOSE = False

#engine = create_engine('sqlite:///database.db', echo=VERBOSE)
engine = create_engine('sqlite://', echo=VERBOSE)
DBBase = declarative_base()
meta = DBBase.metadata
Session = sessionmaker(bind=engine)

# wrapper class (ignored and overwritten for now)
class DBClass:

	def __init_subclass__(cls):
		# create actual subclass of the alchemy base to let alchemy do its thing
		class AlchemyClass(DBBase):
			# always give it an uid
			uid = Column(Integer,primary_key=True,autoincrement=True)
			# generate table name
			__tablename__ = cls.__name__.lower()

		setattr(cls,"__wrapped_alchemy_class__",AlchemyClass)

		# add defined attributes to alchemy class
		for attribute in cls.__dict__:
			if attribute.startswith("__"): continue
			print("Adding attr",attribute)

			val = cls.__dict__[attribute]


	#		# properly model foreign keys
	#		if isinstance(val,Reference):
	#			# add relation with name backref to other class
	#			setattr(val.cls,val.backref,relationship(cls.__wrapped_alchemy_class__, backref = val.cls.__name__.lower(),lazy=False,cascade="all"))
#
#				# add foreign key to this class
#				setattr(cls.__wrapped_alchemy_class__,val.cls.__name__.lower() + "_id",Column(Integer,ForeignKey(val.cls.__wrapped_alchemy_class__.__tablename__ + '.uid')))
#
#			elif isinstance(val,MultiReference):
#				pass
#			else:
#				setattr(AlchemyClass,attribute,val)
			setattr(AlchemyClass,attribute,val)


		def newinit(self,*args,**kwargs):
			# init internal class
			self.alchemy_instance = self.__wrapped_alchemy_class__(*args,**kwargs)
			# db write
			session = Session()
			session.add(self.alchemy_instance)
		cls.__init__ = newinit








DBClass = DBBase
#orig = DBClass.__init_subclass__
#def new_init_subclass(cls):
#	setattr(cls,"uid",Column(Integer,primary_key=True,autoincrement=True))
#	setattr(cls,"__tablename__",cls.__name__.lower())
#	orig(cls)
#DBClass.__init_subclass__ = new_init_subclass

# sentinel to model a foreign key
class Reference():
	def  __init__(self,cls,backref):
		self.cls = cls
		self.backref = backref



# sentinel to model list of references to foreign tables (n-to-m via third table)
class MultiReference():
	def  __init__(self,cls,backref):
		self.cls = cls
		self.backref = backref


def init_database():
	DBBase.metadata.create_all(engine)
