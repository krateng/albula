// changes to the db that are also reflected to the server
// there is no hard requirement for absolute consistency, the server is always authorative



var infos = {
	"artist":{
		type:"artist", //repeating so it's accessible from the object
		url:"/api/artists",
		detail_url:"/api/artist/%ID%",
		primary:e=>e.name,
		secondary_type:null,
		secondary_source:e=>[],
		change:e=>{
			e.sorttitle = e.name.toLowerCase().replace("'","").replace('"','')
		},
		css_class:"artist",
		loaded:false,
		detail_info:[
			{
				name:"Albums",
				type:"album",
				source:e=>e.albums
			},
			{
				name:"Tracks",
				type:"track",
				source:e=>e.tracks
			}
		]
	},
	"album":{
		type: "album",
		url:"/api/albums",
		detail_url:"/api/album/%ID%",
		primary:e=>e.name,
		secondary_type:"artist",
		secondary_source:e=>e.albumartists,
		change:e=>{
			e.sorttitle = e.name.toLowerCase().replace("'","").replace('"','');
		},
		css_class:"album",
		loaded:false,
		detail_info:[
		//	{
		//		name:"Artists",
		//		type:"artists",
		//		source:e=>e.albumartists
		//	},
			{
				name:"Tracks",
				type:"track",
				source:e=>e.tracks
			}
		]
	},
	"track":{
		type: "track",
		url:"/api/tracks",
		detail_url:"/api/track/%ID%",
		primary:e=>e.title,
		secondary_type:"artist",
		secondary_source:e=>e.artists,
		change:e=>{
			e.sorttitle = e.title.toLowerCase().replace("'","").replace('"','');
		},
		css_class:"track",
		loaded:false,
		detail_info:[
			{
				name:"Artists",
				type:"artist",
				source:e=>e.artists
			},
			{
				name:"Albums",
				type:"album",
				source:e=>e.albums
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


var data = {}
var objs = [] //direct id mapping

// populate data from server
for (var type in infos) {
	var info = infos[type]
	var url = info.url

	var xhttp = new XMLHttpRequest();
	// need to save this local because of js late binding
	xhttp.type = type;
	xhttp.info = info;
	xhttp.responseType = "json";
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			//var response = xhttp.responseText;
			var response = this.response;
			//var elements = JSON.parse(response)["result"];
			var elements = response.result
			data[this.type] = elements;
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



function playTrack(id,played) {
	xhttpreq("/api/play",{id:id,seconds:played,time:now()},"POST");
	//update local info
	var track = objs[id];
	track.last_played = now();
	track.times_played += 1;
}
