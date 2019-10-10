function xhttpreq(url,data={},method="GET",callback=function(){},json=true) {
	xhttp = new XMLHttpRequest();

	function curry() {
		if (this.readyState == 4) {
			callback(this);
		}
	}

	xhttp.onreadystatechange = curry;
	xhttp.open(method,url, true);

	body = ""
	if (method == "GET") {
		url += "?";
		for (var key in data) {
			url += encodeURIComponent(key) + "=" + encodeURIComponent(data[key]) + "&";
		}
	}
	else {
		if (json) {
			body = JSON.stringify(data);
			xhttp.setRequestHeader("Content-Type","application/json");
		}
		else {
			for (var key in data) {
				body += encodeURIComponent(key) + "=" + encodeURIComponent(data[key]) + "&";
			}
		}

	}
	xhttp.send(body);
	console.log("Sent!")
}


function now() {
	return Math.floor(Date.now() / 1000);
}






var cookies = {};
var cookiesloaded = false;

function getCookies() {
	cookiestrings = decodeURIComponent(document.cookie).split(';');
	for(var i = 0; i <cookiestrings.length; i++) {
		cookiestrings[i] = cookiestrings[i].trim();
		[key,value] = cookiestrings[i].split("=");
		cookies[key] = value;
	}
	cookiesloaded = true;
}

// always on document load, but call specifically when needed early
document.addEventListener("load",getCookies);

function setCookie(key,val,session=true) {
	if (!cookiesloaded) {
		getCookies();
	}
	cookies[key] = val;
	if (!session) {
		var d = new Date();
 		d.setTime(d.getTime() + (500*24*60*60*1000));
		expirestr = "expires=" + d.toUTCString();
	}
	else {
		expirestr = ""
	}
	document.cookie = encodeURIComponent(key) + "=" + encodeURIComponent(val) + ";" + expirestr;
}

function getCookie(key) {
	if (!cookiesloaded) {
		getCookies();
	}
	return cookies[key];
}

function saveCookies() {
	for (var c in cookies) {
		document.cookie = encodeURIComponent(c) + "=" + encodeURIComponent(cookies[c]);
	}
}
