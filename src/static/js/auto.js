// functions that are automatically assined based on html attributes

SMOOTH_UPDATE = true;
var update_delay = SMOOTH_UPDATE ? 40 : 500;



document.addEventListener('DOMContentLoaded', function() {

	/* SEEKABLE */
	var elements = document.getElementsByClassName("seekable");
	for (var i=0;i<elements.length;i++) {
		callback = elements[i].getAttribute("data-seekcallback");
		elements[i].addEventListener("click",function(evt) {
			elmnt = evt.currentTarget;
			var percentage = evt.offsetX / elmnt.offsetWidth;
			elmnt.firstElementChild.style.width = (percentage * 100) + "%";
			window[callback](percentage);
		})
	}

	/* AUTO UPDATE */
	var elements2 = document.getElementsByClassName("update");
	var functions = []
	for (var i=0;i<elements2.length;i++) {
		updatefunc = elements2[i].getAttribute("data-updatefrom");
		functions.push([elements2[i],updatefunc])
	}


	function supervisor() {
		for (let entry of functions) {
			var [element, func] = entry
			window[func](element); //call function on that element
		}
		setTimeout(supervisor,update_delay);
	}
	supervisor();

}, false);



/* HOTKEYS */

document.addEventListener('keyup', function(evt) {

	var elements = document.querySelectorAll('[data-hotkey]');
	for (let e of elements) {
		if (e.getAttribute("data-hotkey") == evt.code) {
			evt.preventDefault();
			e.onclick();
			break;
		}
	}

}, false);
