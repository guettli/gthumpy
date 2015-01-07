/*
 $Id: gthumpy.js 139 2008-04-23 19:44:21Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/misc/gthumpy.js $
*/
function write_image(image_url) {
  //alert (document.url + ' ' + image_url);
  var image=image_url;
  var match=image_url.match(/^(.*)\.([^.]*)$/);
  if (match) {
	image=match[1] + '_res' + get_size() + '.' + match[2];
  }
  document.write('<img src="' + image + '"/>');
}

function get_size() {
  var match=document.URL.match(/\?size=(\d+)/);
  var size=document.default_size;
  if (!size) {
	throw "default_size unbekannt!";
  }
  if (match) {
	size=match[1];
  }
  return size;
}

function mark_hash(){
  name=window.location.hash.slice(1);
  list=document.getElementsByName(name);
  if (list.length!=1){
	//alert("Cannot find " + name);
	return;
  }
  element=list[0];
  element.style.fontWeight="bold";
  element.style.fontSize="140%";
  window.scrollBy(0, -60);
}

// http://www.quirksmode.org/js/eventSimple.html
function addEventSimple(obj,evt,fn) {
  if (obj.addEventListener)
	obj.addEventListener(evt,fn,false);
  else if (obj.attachEvent)
	obj.attachEvent('on'+evt,fn);
}

function goto_href(link) {
  var match=link.href.match(/size=/);
  if (match){
	// size=... schon in href.
	return false;
  }
  match=link.href.match(/^(.*?)(#.*)?$/);
  if (!match) {
	alert('defekte URL'+link.href);
	return false;
  }
  var rest='';
  if (match[2]) {
	rest=match[2];
  }
  link.href=match[1]+'?size='+get_size()+rest;
  return false;
}
