
function seek(ev,element) {
	 currentPlaylist.sound.seek(currentPlaylist.sound.duration() * ev.clientX / element.offsetWidth);
}

function playtracks(tracks) {
	pause();
	currentPlaylist.sound = null;
	currentPlaylist.list = tracks;
	currentPlaylist.idx = -1;

	play();

}


var currentPlaylist = {
	"list":[],
	"idx":-1,
	"sound":null,
	"loop":false
}


function play() {
	if (currentPlaylist.sound === null) {
		currentPlaylist.idx += 1;
		if (currentPlaylist.list.length <= currentPlaylist.idx) {
			if (currentPlaylist.loop) {currentPlaylist.idx = 0;}
			else {currentPlaylist.idx = -1; pause(); return;}
		}
		currentPlaylist.sound = new Howl({
			src: ["/audioof/" + currentPlaylist.list[currentPlaylist.idx]],
			format: "mp3"
		})
	}
	button = document.getElementById("play_pause_button");
	button.className = "button_pause";
	button.onclick = pause;
	currentPlaylist.sound.play();
	currentPlaylist.sound.on("end",function(){currentPlaylist.sound = null; currentPlaylist.idx += 1; play()})
}
function pause() {
	button = document.getElementById("play_pause_button");
	button.className = "button_play";
	button.onclick = play;
	if (currentPlaylist.sound != null) {
		currentPlaylist.sound.pause();
	}

}


function updateProgressBar() {

	try {
		var prog = currentPlaylist.sound.seek() / currentPlaylist.sound.duration();
		document.getElementById("progressed").style.width = (prog * 100) + "%";
	}
	catch {}

	setTimeout(updateProgressBar,300);
}

updateProgressBar()
