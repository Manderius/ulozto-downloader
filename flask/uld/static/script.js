setInterval(function() { set(httpGet()); console.log("reloaded");}, 500);
function httpGet()
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/text/"+window.location.pathname.split("/download/")[1], false ); // false for synchronous request
    xmlHttp.send( null );
    console.log(window.location.pathname.split("/download/")[1]);
    return xmlHttp.responseText;
}

function set(text) {
    var paragraph = document.getElementById("stdout");
    paragraph.innerHTML = text;
}
