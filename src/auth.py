import secrets
import time
from doreah.settings import get_settings, update_settings
from nimrodel import EAPI
from threading import Lock
from bottle import response as bottleresponse
from bottle import request, HTTPResponse, redirect


authapi = EAPI(path="auth",delay=True)

###

CHALLENGE_BITS = 32
TOKEN_BITS = 32
CYCLE_CHALLENGE = 120
SESSION_EXPIRE = 3600

COMMON = 3590390094909444
GENERATOR = 2
MODULO = """
	FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1
	29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD
	EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245
	E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED
	EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3D
	C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8 FD24CF5F
	83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D
	670C354E 4ABC9804 F1746C08 CA18217C 32905E46 2E36CE3B
	E39E772C 180E8603 9B2783A2 EC07A28F B5C55DF0 6F4C52C9
	DE2BCBF6 95581718 3995497C EA956AE5 15D22618 98FA0510
	15728E5A 8AACAA68 FFFFFFFF FFFFFFFF
"""

### DERIVED

COMMON = hex(COMMON)
MODULO = int(MODULO.replace(" ","").replace("\n","").replace("\t",""),16)

####

challenge_current = None
challenge_old = None
stop_issue = 0
expire = 0
lock = Lock()
updatelock = Lock()

sessions = {} #token -> timestamp expire

def update():
	updatelock.acquire()
	global challenge_current, stop_issue, expire
	now = time.time()
	if now > expire:
		challenge_old = None
		challenge_current = generate_challenge()
		stop_issue = now + CYCLE_CHALLENGE
		expire = stop_issue + CYCLE_CHALLENGE
	elif now > stop_issue:
		challenge_old = challenge_current
		challenge_current = generate_challenge()
		stop_issue = expire #expire value of old challenge is stop issue value of new
		expire = stop_issue + CYCLE_CHALLENGE
	updatelock.release()

def generate_challenge():
	return secrets.token_hex(CHALLENGE_BITS)

def generate_token():
	return secrets.token_hex(TOKEN_BITS)

@authapi.get("challenge")
def get_challenge():
	global challenge_current, stop_issue, expire
	update()
	return {"challenge":challenge_current, "modulo":MODULO,"generator":GENERATOR}


def validate_challenge(challenge,response):
	update()
	lock.acquire()
	if challenge not in [challenge_current, challenge_old]:
		lock.release()
		print("Invalid challenge")
		return False

	pub = str(get_settings("PUBLIC_KEY"))

	if combine(pub,challenge) == combine(response,COMMON):
		# invalidate challenges
		stop_issue = 0
		expire = 0
		update()

		lock.release()
		return True

	else:
		print("Invalid response")
		lock.release()
		return False

@authapi.post("authenticate")
def get_token(challenge,response):
	if validate_challenge(challenge,response):
		token = generate_token()
		sessions[token] = time.time() + SESSION_EXPIRE
		bottleresponse.set_header("Set-Cookie","albulasessiontoken=" + token)# + "; HttpOnly")
		return {"token":token}
	else:
		return {"error":"Access denied."}


def check(request):
	token = request.get_cookie("albulasessiontoken")
	if token is None: return False
	if token not in sessions: return False
	if sessions[token] < time.time(): return False

	sessions[token] = time.time() + SESSION_EXPIRE
	return True

def authenticated(func):

	def newfunc(*args,**kwargs):
		if check(request):
			return func(*args,**kwargs)
		else:
			redirect("/")

	return newfunc

def combine(a,b):
	a = int(a,16)
	b = int(b,16)
	#return (a ** b) % P
	result = pow(a,b,MODULO)
	return hex(result)[2:]

def setpw(password):
	pw = str.encode(password).hex()
	pw1 = combine(hex(GENERATOR),pw)
	pub = combine(pw1,COMMON)
	update_settings("settings/settings.ini",{"PUBLIC_KEY":pub})
