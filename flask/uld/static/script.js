setInterval(function() { set(httpGet()); console.log("reloaded");},100);
function httpGet()
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/text", false ); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
}

function set(text) {
    var paragraph = document.getElementById("stdout");
    paragraph.innerHTML = text;
}
