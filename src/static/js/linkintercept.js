function interceptClickEvent(e) {
    var href;
    var target = e.target || e.srcElement;

    if (target.tagName === 'A' && !target.classList.contains("no-intercept")) {
        href = target.getAttribute('href');


		e.preventDefault();
		history.pushState({},"",href);
		showView();
    }
}


//listen for link click events at the document level
if (document.addEventListener) {
    document.addEventListener('click', interceptClickEvent);
} else if (document.attachEvent) {
    document.attachEvent('onclick', interceptClickEvent);
}
