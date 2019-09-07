function showView() {
	var url_string = window.location.href;
	var url = new URL(url_string);
	var view = url.searchParams.get("view");
//	for (let area of document.getElementsByClassName("content_area")) {
//		area.classList.add("hide")
//	}

	if (view == "tracks") {
		var url = "http://localhost:42051/api/tracks"
	//	document.getElementById("content_area_tracks").classList.remove("hide");
	}
	if (view == "albums") {
		var url = "http://localhost:42051/api/albums"
	//	document.getElementById("content_area_albums").classList.remove("hide");
	}
	if (view == "artists") {
		var url = "http://localhost:42051/api/artists"
	//	document.getElementById("content_area_artists").classList.remove("hide");
	}

	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
	    if (this.readyState == 4 && this.status == 200) {
	       var elements = JSON.parse(xhttp.responseText)["result"];

		   var elements_html = ""

		   infos = {
			   "artists":{primary:e=>e.name,secondary:e=>"",singular:"artist"},
			   "albums":{primary:e=>e.name,secondary:e=>e.albumartist,singular:"album"},
			   "tracks":{primary:e=>e.title,secondary:e=>e.artists.map(a=>a.name).join(", "),singular:"track"}
		   }

		   for (var i=0;i<elements.length;i++) {
			   element = elements[i]
			   console.log(element)
			   info = infos[view]
			   elements_html += `
			   <div class="content_element ` + info.singular + `">
				   <table>
					   <tr class="image"><td style="background-image:url('/imgof/` + element.uid + `');">
					   </td></tr>
					   <tr class="secondary_info"><td>
						   <span title="` + info.secondary(element) + `">` + info.secondary(element) + `</span>
					   </td></tr>
					   <tr class="main_info"><td>
						   <span onclick="lnk('view','album','id',` + element.uid + `)" title="` + info.primary(element) + `">` + info.primary(element) + `</span>
					   </td></tr>
				   </table>
			   </div>
			   `

		   }

		   document.getElementById("content_area").innerHTML = elements_html;
	    }
	};
	xhttp.open("GET", url, true);
	xhttp.send();


	/* sort
	var areas = document.getElementsByClassName("content_area");
	for (var i=0;i<areas.length;i++) {
		var elements = areas[i].getElementsByClassName("content_element");
		elements.sort(function(a,b) {
			var text_a = a.getElementsByClassName("main_info")[0].children[0].children[0].innerHTML();
			var text_b = b.getElementsByClassName("main_info")[0].children[0].children[0].innerHTML();
			return a == b ? 0 : (a > b ? 1 : -1);
		})

		for (i = 0; i < elements.length; i++) {
		  areas[i].appendChild(elements[i]);
		}

	} */


}



function lnk() {
	var searchParams = new URLSearchParams(window.location.search);
	// arguments as object
	if (arguments.length == 1 && typeof arguments[0] === 'object') {
		var args = arguments[0];
	}
	// arguments as tuple
	else {

		var args = {};
		for (var i=0;i < arguments.length;i += 2) {
			args[arguments[i]] = arguments[i+1];
		}
	}

	for (var key in args) {
		searchParams.set(key, args[key]);
	}
	history.pushState({},"","?" + searchParams.toString());
	showView();
}
