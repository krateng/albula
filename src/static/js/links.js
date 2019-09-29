function createLink(type,obj) {
	//return `<span onclick=lnk('view','detail','type','` + type + `','id',` + obj.id + `) >` + obj.name + `</span>`

	return `<a href="?view=detail&type=` + type + `&id=` + obj.id + `">` + obj.name + `</a>`
}

function createLinks(type,objs,sep) {
	var links = [];
	for (var i=0;i<objs.length;i++) {
		links.push(createLink(type,objs[i]));
	}
	return links.join(sep);
}
