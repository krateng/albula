
var infos = {
	"artists":{
		url:"/api/artists",
		primary:e=>e.name,
		secondary:e=>[],
		change:e=>{
			e.sorttitle = e.name.toLowerCase()
		},
		singular:"artist",
		loaded:false
	},
	"albums":{
		url:"/api/albums",
		primary:e=>e.name,
		secondary:e=>e.albumartist_names,
		secondary_ids:e=>e.albumartist_ids,
		change:e=>{
			e.sorttitle = e.name.toLowerCase();
		},
		singular:"album",
		loaded:false
	},
	"tracks":{
		url:"/api/tracks",
		primary:e=>e.title,
		secondary:e=>e.artist_names,
		secondary_ids:e=>e.artist_ids,
		change:e=>{
			e.sorttitle = e.title.toLowerCase()
		},
		singular:"track",
		loaded:false
	}
}

var sortings = {
	"alphabet":e=>e.sorttitle,
	"last":e=>-e.last_played,
	"most":e=>-e.times_played
}

var sortingfuncs = {}

for (var s in sortings) {
	sorting = sortings[s]
	function compare(s,a,b) {
		var a_ = s(a);
		var b_ = s(b);
		if (a_==b_) {return 0;}
		return (a_>b_) ? 1 : -1;
	}
	sortingfuncs[s] = compare.bind(null,sorting); // bind parameter s
}

//console.log(sortingfuncs)


var data = {}
var objs = [] //direct id mapping

// populate data from server
for (var view in infos) {
	var info = infos[view]
	var url = info.url

	var xhttp = new XMLHttpRequest();
	// need to save this local because of js late binding
	xhttp.view = view;
	xhttp.info = info;
	xhttp.responseType = "json";
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			//var response = xhttp.responseText;
			var response = this.response;
			//var elements = JSON.parse(response)["result"];
			var elements = response.result
			data[this.view] = elements;
			for (let el of elements) {
				this.info.change(el); //apply all local data preparations
				objs[el.uid] = el;
			}
			this.info.loaded = true
		}
	};
	xhttp.open("GET", url, true);
	xhttp.send();
}


function showView() {

	var url_string = window.location.href;
	var url = new URL(url_string);
	var view = url.searchParams.get("view") || "albums";
	var sortby = url.searchParams.get("sort") || "alphabet";


	var info = infos[view]
	var elements = data[view]

	if (!info.loaded) {
		setTimeout(showView,100);
		return;
	}


	var elements_html = ""

	elements.sort(sortingfuncs[sortby]);
	//console.log(elements)

   for (var i=0;i<elements.length;i++) {
		element = elements[i]
		//console.log(element)

		secondary_info_html = [];
		for (var j=0;j<info.secondary(element).length;j++) {
			secondary_info_html.push(`<span onclick="lnk('view','artist','id',` + info.secondary_ids(element)[j] + `)">` +
				info.secondary(element)[j] + `</span>`)
		}

		elements_html += `
		<div class="content_element ` + info.singular + `">
		   <table>
				<tr class="image"><td onclick="setPlaylist([` + element.track_ids.join(",") + `])">
					<div class="artwork" style="background-image:url('/imgof/` + element.uid + `');"></div>
					<div class="hover"></div>
				</td></tr>
				<tr class="secondary_info"><td>` + secondary_info_html.join(" | ") + `
				</td></tr>
				<tr class="main_info"><td>
					<span onclick="lnk('view','album','id',` + element.uid + `)" title="` + info.primary(element) + `">` + info.primary(element) + `</span>
				</td></tr>
			</table>
		</div>
		`

	}

	document.getElementById("content_area").innerHTML = elements_html;


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
