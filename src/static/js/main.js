
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
		secondary_singular:"artist",
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
		secondary_singular:"artist",
		loaded:false
	}
}


var detailinfos = {
	"artist": {
		url:"api/artist/%ID%",
		primary:e=>e.artist.name,
		secondary:e=>[],
		page_parts:[
			{
				name:"Albums",
				type:"albums",
				source:e=>e.albums
			},
			{
				name:"Tracks",
				type:"tracks",
				source:e=>e.tracks
			}
		]
	},
	"album":{
		url:"api/album/%ID%",
		primary:e=>e.album.name,
		secondary:e=>e.album.albumartist_names,
		secondary_ids:e=>e.album.albumartist_ids,
		secondary_singular:"artist",
		page_parts:[
		//	{
		//		name:"Artists",
		//		type:"artists",
		//		source:e=>e.albumartists
		//	},
			{
				name:"Tracks",
				type:"tracks",
				source:e=>e.tracks
			}
		]
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


function renderElements(elements,info) {

	var elements_html = ""

	for (var i=0;i<elements.length;i++) {
		 element = elements[i]
		 //console.log(element)

		 secondary_info_html = [];
		 for (var j=0;j<info.secondary(element).length;j++) {
			 secondary_info_html.push(`<span onclick="lnk('view','` + info.secondary_singular + `','id',` + info.secondary_ids(element)[j] + `)">` +
				 info.secondary(element)[j] + `</span>`)
		 }

		 elements_html += `
		 <div class="content_element ` + info.singular + `">
			<table>
				 <tr class="image"><td onclick="setPlaylist([` + element.track_ids.join(",") + `])">
					 <div class="artwork" style="background-image:url('/imgof/` + element.uid + `');"></div>
					 <div class="hover"></div>
				 </td></tr>
				 <tr class="secondary_info"><td>` + secondary_info_html.join(" | ") + `<span></span>
				 </td></tr>
				 <tr class="main_info"><td>
					 <span onclick="lnk('view','` + info.singular + `','id',` + element.uid + `)" title="` + info.primary(element) + `">` + info.primary(element) + `</span>
				 </td></tr>
			 </table>
		 </div>
		 `

	 }

	 return elements_html;
}


function showView() {

	var url_string = window.location.href;
	var url = new URL(url_string);
	var view = url.searchParams.get("view") || "albums";
	var sortby = url.searchParams.get("sort") || "alphabet";

	if (["albums","artists","tracks"].includes(view)) {
		var info = infos[view]
		var elements = data[view]

		if (!info.loaded) {
			setTimeout(showView,100);
			return;
		}




		elements.sort(sortingfuncs[sortby]);
		//console.log(elements)

	   elements_html = renderElements(elements,info);

		document.getElementById("content_area").innerHTML = elements_html;
	}


	else {
		var info = detailinfos[view];
		var id = url.searchParams.get("id");
		var url = info.url.replace("%ID%",id)

		var xhttp = new XMLHttpRequest();
		// need to save this local because of js late binding
		xhttp.view = view;
		xhttp.info = info;
		xhttp.id = id;
		xhttp.responseType = "json";
		xhttp.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				//var response = xhttp.responseText;
				var response = this.response;
				console.log(response)


				var secondary_elements = []
				for (var i=0;i<this.info.secondary(response).length;i++) {
					secondary_elements.push(`<span onclick="lnk('view','` + this.info.secondary_singular + `','id',` + this.info.secondary_ids(response)[i] + `)">` + this.info.secondary(response)[i] + `</span>`)
				}
				var html = secondary_elements.join(" | ") + `
					<h1>` + this.info.primary(response) + `</h1>`


				var html = `
				<table class="top_info">
					<tr>
						<td class="image">
							<div style="background-image:url('/imgof/` + this.id + `')"></div>
						</td>
						<td class="text">
							<span>` + secondary_elements.join(" | ") + `</span><br/>
							<h1>` + this.info.primary(response) + `</h1>
						</td>
					</tr>
				</table>
				`


				for (var j=0;j<this.info.page_parts.length;j++) {
					e = this.info.page_parts[j];
					html += `<h2>` + e.name + `</h2>`;
					elements = e.source(response);
					einfo = infos[e.type];

					html += renderElements(elements,einfo);

				}

				document.getElementById("content_area").innerHTML = html;






			}
		};
		xhttp.open("GET", url, true);
		xhttp.send();
	}



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
