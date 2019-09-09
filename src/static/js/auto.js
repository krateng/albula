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
}, false);
