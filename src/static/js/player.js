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
	track = objs[list[idx]];
	sound = new Howl({
		src: ["/audioof/" + list[idx]],
		format: "mp3"
	});
	sound.on("end",done)

	document.getElementById("current_track_artwork").style.backgroundImage = "url('/imgof/" + list[idx] + "')";
	document.getElementById("current_track_title").innerHTML = track.title;
	document.getElementById("current_track_artists").innerHTML = track.artist_names.join(", ");
}

function done() {
	pause();
	xhttpreq("/api/play",data={id:list[idx]},method="POST");
	sound = null;
	if (next()) {
		initSound();
		play();
	}
	else {
		document.getElementById("current_track_artwork").style.backgroundImage = "none";
		document.getElementById("current_track_title").innerHTML = "";
		document.getElementById("current_track_artists").innerHTML = "";
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
