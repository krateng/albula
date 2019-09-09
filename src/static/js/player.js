var list = [];
var idx = 0;
var playing = false;
var loop = false;
var random = false;
var sound = null;

function play() {
	if (sound != null) {
		sound.play();
	}
	console.log("Playing element",idx,"of",list)

	button = document.getElementById("play_pause_button");
	button.className = "button_pause";
	button.onclick = pause;
}
function pause() {
	if (sound != null) {
		sound.pause()
	}

	button = document.getElementById("play_pause_button");
	button.className = "button_play";
	button.onclick = play;
}

function setPlaylist(lst) {
	pause();
	list = lst;
	idx = 0;
	initSound();
	play();
}

function next() {
	idx += 1;
	if (idx >= list.length) {
		if (loop) {
			idx = 0;
			return true;
		}
		else {
			list = [];
			return false;
		}
	}
	return true;
}

function initSound() {
	sound = new Howl({
		src: ["/audioof/" + list[idx]],
		format: "mp3"
	});
	sound.on("end",done)
}

function done() {
	pause();
	sound = null;
	if (next()) {
		initSound();
		play();
	}

}



function seek(ev,element) {
	 sound.seek(sound.duration() * ev.offsetX / element.offsetWidth);
}

function changeVolume(prct) {
	Howler.volume(prct);
}


function updateProgressBar(element) {
	try {
		prog = sound.seek() / sound.duration();
	}
	catch {
		prog = 0;
	}

	element.style.width = (prog * 100) + "%";
}
