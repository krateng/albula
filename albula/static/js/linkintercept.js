// This intercepts all clicks on links and applies the native function instead of
// loading that page the proper way (because the music shouldn't stop)
// Credit to Stack Overflow user 607332/james

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
