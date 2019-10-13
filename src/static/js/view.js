var currentObj = null;

function getCurrent() { return currentObj; }


function renderElements(elements,info) {

	var elements_html = ""

	for (var i=0;i<elements.length;i++) {
		 element = elements[i]
		 //console.log(element)

		 secondary_info_html = [];
		 secondary_info = infos[info.secondary_type];
		 for (var j=0;j<info.secondary_source(element).length;j++) {
			 secondary_element = info.secondary_source(element)[j];
			 secondary_info_html.push(
			//	 `<span onclick="lnk('view','detail','type','` + secondary_info.type + `','id',` + secondary_element.id + `)">` +
			//	 secondary_element.name + `</span>`)
				`<a href="?view=detail&type=` + secondary_info.type + "&id=" + secondary_element.id + `">` +
				secondary_element.name + `</a>`)
		 }

		 elements_html += `
		 <div class="content_element ` + info.css_class + `">
			<table>
				<tr class="image"><td>
				 	<div class="artwork" style="background-image:url('` + element.artwork + `');"></div>
					<div title="Play" class="element_play" onclick="setPlaylist(` + element.uid + `)"></div>
					<div title="Add to queue"  class="element_append" onclick="appendPlaylist(` + element.uid + `)"></div>
 					<div title="Play next" class="element_insert" onclick="insertPlaylist(` + element.uid + `)"></div>
				 </td></tr>
				 <tr class="secondary_info"><td>` + secondary_info_html.join(" | ") + `<span>&nbsp;</span>
				 </td></tr>
				 <tr class="main_info"><td>
					 <span title="` + info.primary(element).replace(/"/g,'&quot;') + `"><a href="?view=detail&type=` + info.type + `&id=` + element.uid + `">` + info.primary(element) + `</a></span>
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

	if (!url.searchParams.get("view") ||
		!url.searchParams.get("type") ||
		(!url.searchParams.get("sort")) && url.searchParams.get("view") == "list") {
			url.searchParams.set("view",url.searchParams.get("view") || "list");
			url.searchParams.set("type",url.searchParams.get("type") || getCookie("viewtype") || "album");
			url.searchParams.set("sort",url.searchParams.get("sort") || getCookie("sort") || "alphabet");

			history.pushState({},"","?" + url.searchParams.toString());
	}



	var view = url.searchParams.get("view");
	var type = url.searchParams.get("type");
	var sortby = url.searchParams.get("sort");

	if (sortby != null) { setCookie("sort",sortby); }
	if (type != null) { setCookie("viewtype",type); }

	if (view == "list") {
		currentObj = null
		var info = infos[type]
		var elements = data[type]

		if (!info.loaded) {
			setTimeout(showView,100);
			return;
		}




		elements.sort(sortingfuncs[sortby]);
		//console.log(elements)

	   elements_html = renderElements(elements,info);

		document.getElementById("content_area").innerHTML = elements_html;

		document.title = "Albula";
	}


	else if (view == "detail") {
		var info = infos[type];
		var id = url.searchParams.get("id");
		var url = info.detail_url.replace("%ID%",id)
		currentObj = id

		var xhttp = new XMLHttpRequest();
		// need to save this local because of js late binding
		xhttp.type = type;
		xhttp.info = info;
		xhttp.id = id;
		xhttp.responseType = "json";
		xhttp.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				//var response = xhttp.responseText;
				var response = this.response;
				//console.log(response)


				element_info = response[type] //direct info is always saved in a subelement of same name in the dict

				secondary_info_html = [];
				secondary_info = infos[info.secondary_type];
				for (var i=0;i<this.info.secondary_source(element_info).length;i++) {
					secondary_element = this.info.secondary_source(element_info)[i];
					secondary_info_html.push(
				//		`<span onclick="lnk('view','detail','type','` + secondary_info.type + `','id',` + secondary_element.id + `)">` +
				//		secondary_element.name + `</span>`)
						`<a href="?view=detail&type=` + secondary_info.type + `&id=` + secondary_element.id + `">` +
						secondary_element.name + `</a>`);
				}


				artworks_html = [];
				for (var i=0;i<element_info.artwork_choices.length;i++) {
					choice = element_info.artwork_choices[i];
					id = choice.split("/").slice(-1)[0]
					artworks_html.push(`<td style="background-image:url('` + choice + `');"
					onmouseover="document.getElementById('main_image').style.backgroundImage='url(\\'` + choice + `\\')';"
					onmouseout="document.getElementById('main_image').style.backgroundImage='url(\\'` + element_info.artwork + `\\')';"
					onclick="setArtwork(` + this.id + `,` + id + `);showView();">
					</td>`)
				}



				var html = `
				<table class="top_info ` + this.type + `_info">
					<tr>
						<td class="image">
							<div id="main_image" style="background-image:url('` + element_info.artwork + `')"></div>
						</td>
						<td class="text">
							<span>` + secondary_info_html.join(" | ") + `</span><br/>
							<h1 contenteditable="true" onfocusout="setName(` + this.id + `,this.innerHTML)">` + this.info.primary(element_info) + `</h1>
							<br/><br/><br/>
							<table class="image_row" id="image_choices"><tr>` + artworks_html.join("") + `</tr></table>
						</td>
					</tr>
				</table>
				`


				for (var j=0;j<this.info.detail_info.length;j++) {
					e = this.info.detail_info[j];
					html += `<h2>` + e.name + `</h2>`;

					einfo = infos[e.type];
					elements = e.source(response);
					for (let el of elements) {
						einfo.change(el); //apply all local data preparations
					}
					elements.sort(sortingfuncs[sortby]);


					html += renderElements(elements,einfo);

				}

				document.getElementById("content_area").innerHTML = html;

				document.getElementById("content_area").scrollTo(0,0);

				document.title = this.info.primary(element_info) + " - Albula";






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
