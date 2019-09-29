function pw_to_hex(pw) {
	var utf8 = unescape(encodeURIComponent(pw));
	var arr = [];
	for (var i = 0; i < utf8.length; i++) {
	    arr.push(utf8.charCodeAt(i));
	}
	return arr.reduce((output, elem) => (output + ('0' + elem.toString(16)).slice(-2)),'');
}


function solve(generator,challenge,pw,modulo) {
	pw = pw_to_hex(pw);
	//console.log("challenge: " + challenge + ", pw: " + pw);
	//pw = parseInt(pw,16);
	pw = BigInt("0x" + pw);
	//challenge = parseInt(challenge,16);
	challenge = BigInt("0x" + challenge);
	modulo = BigInt(modulo);
	var res1 = expmod(generator,pw,modulo);
	var result = expmod(res1,challenge,modulo);
	//result = pw.modPow(challenge,modulo)
	//console.log("result: " + result)
	//console.log(result)
	return result.toString(16);
}

function expmod( base, exp, mod ){
  if (exp == 0n) return 1n;
  if (exp % 2n == 0n){
    //return Math.pow( expmod( base, (exp / 2n), mod), 2n) % mod;
    return (expmod(base,(exp/2n),mod) ** 2n) % mod;
  }
  else {
    return (base * expmod( base, (exp - 1n), mod)) % mod;
  }
}


function update(generator,challenge,modulo) {
	pw = document.getElementById("password").value;
	if (pw == "") {
		var resp = "";
	}
	else {
		var resp = solve(generator,challenge,pw,modulo);
	}

	document.getElementById("response").value = resp;
}




function auth() {
	var response = document.getElementById("response").value;
	var challenge = document.getElementById("challenge").innerHTML;

	xhttpreq("/auth/authenticate",data={"response":response,"challenge":challenge},method="POST",callback=checkAuth);
}

function checkAuth(response) {
	var res = JSON.parse(response.responseText);
	console.log(res);
	if (res.hasOwnProperty("token")) {
		console.log("Login!")
		var token = res["token"];
		document.cookie = "albulasessiontoken=" + token;
		location.assign("/");
	}
}

function enterpress(evt) {
	if (evt.keyCode === 13) {
		auth();
	}
}
