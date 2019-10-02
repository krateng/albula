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
