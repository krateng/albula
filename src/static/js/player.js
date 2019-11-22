var list = [];
var idx = 0;
var currently_playing = false;
var loop = false;
var random = false;
var sound = null;
var played = 0;



// helper functions to abstract timekeeping into a clock analogy
var lastUpdate = 0;
var ticking = false;

function startClock() {
	if (!ticking) {
		ticking = true;
		lastUpdate = neo.now();
	}

}
function stopClock() {
	if (ticking) {
		var passed = neo.now() - lastUpdate;
		played += passed;
		ticking = false;
	}

}

function updateList() {
	for (var i=1;i<5;i++) {
		try {
			var next = objs[list[idx+i]];
			document.getElementById("next_" + i).innerHTML = createLinks("artist",next.artists,", ") + " - " + next.title;
		}
		catch {

		}
	}
	if (idx + 1 >= list.length) {
		document.getElementById("next_tracks_label").classList.add("hide");
	}
	else {
		document.getElementById("next_tracks_label").classList.remove("hide");
	}
}


// need to do this for correct event listener below
function nxt() {
	next();
}

function preloadNext() {
	if (list.length > idx+1) {
		nextsound = new Howl({
			src: ["/audioof/" + list[idx+1]],
			format: "mp3"
		});
	}
}

// function should always be called when new track becomes current one. inits sound object and fills in metadata
function initSound(startplay=false) {

	sound = new Howl({
		src: ["/audioof/" + list[idx]],
		format: "mp3"
	});
	if (startplay) {
		play()
	}
	sound.on("end",nxt);
	track = objs[list[idx]];



	document.getElementById("current_track_artwork").style.backgroundImage = "url('" + track.artwork + "')";
	document.getElementById("current_track_title").innerHTML = track.title;
	document.getElementById("current_track_artists").innerHTML = createLinks("artist",track.artists,", ");

	updateList();



	played = 0;



	// preloading next sound for smooth transition, don't need to actually keep reference,
	// just make sure howler has it loaded once
	preloadNext();
}


// function should always be called when track stops being current one.
// returns whether track was playing before
function uninitSound() {

	stopClock();

	wasplaying = false

	// queue non-urgent things asynchronously for better gapless playback
	post = postUninit.bind(null,sound,list,idx,played);
	setTimeout(post,1000);

	if (sound != null) {
		wasplaying = sound.playing;
		sound.stop();
		sound = null;
	}
	pause();

	document.getElementById("current_track_artwork").style.backgroundImage = "none";
	document.getElementById("current_track_title").innerHTML = "";
	document.getElementById("current_track_artists").innerHTML = "";

	document.getElementById("next_1").innerHTML = "";
	document.getElementById("next_2").innerHTML = "";
	document.getElementById("next_3").innerHTML = "";
	document.getElementById("next_4").innerHTML = "";

	return wasplaying;
}

function postUninit(sound,list,idx,played) {
	if (sound != null) {
		// always unload to free memory
		sound.unload();
		playTrack(list[idx],played);

	}
}


// play current track at current position
function play() {
	if (sound != null) {
		sound.play();
		startClock();
	}
	//console.log("Playing element",idx,"of",list)

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


// if these receive a single number instead of a playlist, they interpret it as the object
function setPlaylist(lst) {
	if (!Array.isArray(lst)) {
		lst = objs[lst].track_ids;
	}
	pause();
	uninitSound();
	list = lst;
	idx = 0;
	initSound();
	play();
}
function appendPlaylist(lst) {
	if (!Array.isArray(lst)) {
		lst = objs[lst].track_ids;
	}
	list = list.concat(lst);
	updateList();
	preloadNext();
}
function insertPlaylist(lst) {
	if (!Array.isArray(lst)) {
		lst = objs[lst].track_ids;
	}
	list = list.slice(0,idx+1).concat(lst).concat(list.slice(idx+1));
	updateList();
	preloadNext();
}
function setPlaylistRandom(lst) {
	if (!Array.isArray(lst)) {
		lst = objs[lst].track_ids;
	}
	lst = lst.slice()
	for (var i = lst.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        [lst[i],lst[j]] = [lst[j],lst[i]];
    }
	setPlaylist(lst);
}
function setPlaylistWeightedRandom(lst) {
	if (!Array.isArray(lst)) {
		lst = objs[lst].track_ids;
	}
	lst = lst.slice()
	len = lst.length;
	for (var i=0;i<len;i++) {
		var track = objs[lst[i]]
		for (var j=0;j<track.times_played;j++) {
			lst.push(lst[i])
		}
	}
	setPlaylistRandom(lst);
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






function seek(prct) {
	var element = document.getElementById("progressbar")
	 sound.seek(sound.duration() * prct);
}

function changeVolume(prct) {
	Howler.volume(prct);
	neo.setCookie("volume",prct);
}
function getVolume() {
	return Howler._volume;
}
changeVolume(neo.getCookie("volume"));
document.addEventListener("DOMContentLoaded",function() {
	document.getElementById("volume").style="width:" + Number(neo.getCookie("volume"))*100 + "%;";
});



function updateProgressBar(element) {
	try {
		prog = sound.seek() / sound.duration();
	}
	catch {
		prog = 0;
	}

	element.style.width = (prog * 100) + "%";
}
