var list = [];
var idx = 0;
var playing = false;
var loop = false;
var random = false;
var sound = null;
var played = 0;



// helper functions to abstract timekeeping into a clock analogy
var lastUpdate = 0;
var ticking = false;
function now() {
	return Math.floor(Date.now() / 1000);
}
function startClock() {
	if (!ticking) {
		ticking = true;
		lastUpdate = now();
	}

}
function stopClock() {
	if (ticking) {
		var passed = now() - lastUpdate;
		played += passed;
		ticking = false;
	}

}




// function should always be called when new track becomes current one. inits sound object and fills in metadata
function initSound(startplay=false) {
	track = objs[list[idx]];
	sound = new Howl({
		src: ["/audioof/" + list[idx]],
		format: "mp3"
	});
	sound.on("end",next)

	document.getElementById("current_track_artwork").style.backgroundImage = "url('/imgof/" + list[idx] + "')";
	document.getElementById("current_track_title").innerHTML = track.title;
	document.getElementById("current_track_artists").innerHTML = track.artist_names.join(", ");

	for (var i=1;i<5;i++) {
		try {
			var next = objs[list[idx+i]]
			document.getElementById("next_" + i).innerHTML = next.artist_names.join(", ") + " - " + next.title;
		}
		catch {

		}
	}



	played = 0;

	if (startplay) {
		play()
	}
}


// function should always be called when track stops being current one.
// returns whether track was playing before
function uninitSound() {

	stopClock();
	xhttpreq("/api/play",{id:list[idx],seconds:played,time:now()},"POST");
	//update local info, doesn't necessarily need to be exactly consistent with db, just for
	//sorting and stuff
	var track = objs[list[idx]];
	track.last_played = now();
	track.times_played += 1;


	playing = false
	if (sound != null) {
		playing = sound.playing;

		if (sound.state() != "loaded") {
			// Stopping a sound before it's loaded will mean it will still play later
			sound.unload();
		}
		else {
			sound.stop();
		}
		sound = null;
	}

	document.getElementById("current_track_artwork").style.backgroundImage = "none";
	document.getElementById("current_track_title").innerHTML = "";
	document.getElementById("current_track_artists").innerHTML = "";

	document.getElementById("next_1").innerHTML = "";
	document.getElementById("next_2").innerHTML = "";
	document.getElementById("next_3").innerHTML = "";
	document.getElementById("next_4").innerHTML = "";

	return playing;
}


// play current track at current position
function play() {
	if (sound != null) {
		sound.play();
		startClock();
	}
	console.log("Playing element",idx,"of",list)

	button = document.getElementById("play_pause_button");
	button.className = "button_pause";
	button.onclick = pause;

}



// pause current playback
function pause() {
	if (sound != null) {
		sound.pause();
		stopClock();
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


// change current track. init sound object and put metadata in etc

function next() {
	playing = uninitSound();
	idx += 1;
	if (idx >= list.length) {
		if (loop) {
			idx = 0;
			initSound(playing);
			return true;
		}
		else {
			list = [];
			return false;
		}
	}
	initSound(playing);
	return true;
}

function prev() {
	playing = uninitSound();
	idx -= 1;
	if (idx < 0) {
		if (loop) {
			idx = list.length - 1;
			initSound(playing);
			return true;
		}
		else {
			list = [];
			return false;
		}
	}
	initSound(playing);
	return true;
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
