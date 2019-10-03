// functions that are automatically assined based on html attributes

document.addEventListener('DOMContentLoaded', function() {
	elements = document.getElementsByClassName("seekable");
	for (var i=0;i<elements.length;i++) {
		callback = elements[i].getAttribute("data-seekcallback");
		elements[i].addEventListener("click",function(evt) {
			elmnt = evt.currentTarget;
			var percentage = evt.offsetX / elmnt.offsetWidth;
			elmnt.firstElementChild.style.width = (percentage * 100) + "%";
			window[callback](percentage);
		})
	}

	elements2 = document.getElementsByClassName("update");
	functions = []
	for (var i=0;i<elements2.length;i++) {
		updatefunc = elements2[i].getAttribute("data-updatefrom");
		functions.push([elements2[i],updatefunc])
	}


	function supervisor() {
		for (let entry of functions) {
			var [element, func] = entry
			window[func](element); //call function on that element
		}
		setTimeout(supervisor,40);
	}
	supervisor();

}, false);
