setInterval(function() { set(httpGet()); console.log("reloaded");}, 500);
function httpGet()
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/status", false ); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
}

function set(text) {
    var paragraph = document.getElementById("overview");
    paragraph.innerHTML = text;
}
