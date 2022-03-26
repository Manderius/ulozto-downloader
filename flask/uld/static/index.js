setInterval(function() { httpGet(); }, 1000);

function httpGet()
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/status", true ); // false for synchronous request
    xmlHttp.responseType = 'json';
    xmlHttp.onload = function() {
        set(xmlHttp.response);
    }
    xmlHttp.send( null );
}

rows = {}

function createRow(id) {
    const template = `<tr>
        <td id="${id}_filename">Zahajuji stahování...</td>
        <td class="align-middle">
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
    row.firstElementChild.style.cursor = 'pointer';
    row.firstElementChild.onclick = function () {
        window.location = "/download/" + id; 
    }
    var tbody = document.getElementById("files");
    tbody.appendChild(row);
}

function createNode(htmlString) {
    var div = document.createElement('tbody');
    div.innerHTML = htmlString.trim();
    return div.firstChild;
}

function set(text) {
    for (var file of text) {
    	if (!(file.id in rows)) {
    		createRow(file.id);
    	}
        setInnerHtml(file.id, 'filename', trimFileName(file.filename))
        setProgress(file.id, file.percent)
        setSize(file.id, file.downloadedSize, file.totalSize)
        setInnerHtml(file.id, 'speed', (file.currSpeed.toFixed(3)) + " MB/s")
        setInnerHtml(file.id, 'time', file.remainingTime)
    }
}

function trimFileName(filename) {
    var max = 34;
    if (filename.length > max + 6) {
        return filename.substring(0, max) + "..." + filename.substring(filename.length - 3)
    }
    return filename;
}

function setProgress(id, percent) {
    perc = Math.floor(percent)
    document.getElementById(`${id}_progress`).style.width = perc + '%'
    document.getElementById(`${id}_percentage`).innerHTML = perc + ' %'
}

function setSize(id, downSize, totalSize) {
    dSize = Math.floor(downSize)
    tSize = Math.floor(totalSize)
    setInnerHtml(id, 'size', `${dSize} / ${tSize} MB`)
}

function setInnerHtml(id, childId, value) {
	document.getElementById(id + "_" + childId).innerHTML = value;
}
