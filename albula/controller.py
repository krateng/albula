import os
from .__init__ import DATA_DIR
os.chdir(DATA_DIR)

import getpass
from doreah.control import mainfunction


def setpassword():
	print("Input new password")
	pw = getpass.getpass()
	print("Repeat please")
	if pw != getpass.getpass():
		print("Passwords do not match!")
	else:
		from doreah import auth
		auth.defaultuser.setpw(pw)

def updateplays():
	from .db import db, Track
	from .dbbuild.malojareader import get_scrobbles


	tracks = db.getall(Track)
	get_scrobbles(tracks)
	db.save()

@mainfunction({},shield=True)
def main(action,**kwargs):
	actions = {
		"setpassword":setpassword,
		"updateplays":updateplays
	}

	return actions[action](**kwargs)
