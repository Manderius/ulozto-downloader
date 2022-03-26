//setInterval(function() { set(httpGet()); console.log("reloaded");}, 5000);
// function httpGet()
// {
//     return [{"id": "grefdsa", "filename": "Avengers-2-Vek-Ultrona-Avengers-Age-of-Ultron-2015-CZ-dabing.avi", "downloadedSize": 54454746.57421875, "totalSize": 785254544, "percent": 28.4772770853268695, "avgSpeed": 0.4889176436685756, "currSpeed": 0.6533434213073841, "remainingTime": "0:25:24"}];
// }

setInterval(function() { set(httpGet()); console.log("reloaded");}, 1000);
function httpGet()
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/status", false ); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.response;
}

rows = {}

function createRow(id) {
    const template = `<tr>
        <td id="${id}_filename">Zahajuji stahování...</td>
        <td>
            <div class="progress">
                <div class="progress-bar position-relative" role="progressbar"
                aria-valuemin="0" aria-valuemax="100" style="width: 0%" id="${id}_progress">
                </div>
            </div>
        </td>
        <td id="${id}_percentage">0 %</td>
        <td id="${id}_size">0 / 0 MB</td>
        <td id="${id}_speed">0 MB/s</td>
        <td id="${id}_time">0:00:00</td>
    </tr>`;
	row = createNode(template);
  rows[id] = row;
  var tbody = document.getElementById("files");
  tbody.appendChild(row)
}

function createNode(htmlString) {
    var div = document.createElement('tbody');
    div.innerHTML = htmlString.trim();
    return div.firstChild;
}

function set(text) {
    var tbody = document.getElementById("files");
    console.log(text)
    if (text.length == 0) return;
    for (var file of text) {
    	if (!(file.id in rows)) {
    		createRow(file.id);
    	}
        console.log(file)
        setInnerHtml(file.id, 'filename', file.filename)
        setProgress(file.id, file.percent)
        setSize(file.id, file.downloadedSize, file.totalSize)
        setInnerHtml(file.id, 'speed', (file.currSpeed.toFixed(3)) + " MB/s")
        setInnerHtml(file.id, 'time', file.remainingTime)
    }
    
}

function setProgress(id, percent) {
    perc = Math.floor(percent)
    document.getElementById(`${id}_progress`).style.width = perc + '%'
    document.getElementById(`${id}_percentage`).innerHTML = perc + ' %'
}

function setSize(id, downSize, totalSize) {
bytesToMB = 1024 * 1024;
    dSize = Math.floor(downSize / bytesToMB)
    tSize = Math.floor(totalSize / bytesToMB)
    setInnerHtml(id, 'size', `${dSize} / ${tSize} MB`)
}

function setInnerHtml(id, childId, value) {
	document.getElementById(id + "_" + childId).innerHTML = value;
}

set(httpGet())
