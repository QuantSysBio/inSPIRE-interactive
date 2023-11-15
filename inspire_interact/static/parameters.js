function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  ev.dataTransfer.setData("text", ev.target.id);
}

function drop(ev) {
  ev.preventDefault();
  var data = ev.dataTransfer.getData("text");
  ev.target.appendChild(document.getElementById(data));
}

function addRawFiles(rawFiles) {
    for (i = 0; i < rawFiles.length; i++) {
        //gets cells of current row
        var newDiv = document.createElement("div");
        newDiv.id = "draggable" + i;
        newDiv.draggable=true;
        newDiv.ondragstart="drag(event)";
        var newContent = document.createTextNode(rawFiles[i]);
        newDiv.appendChild(newContent);
        if (i == 0) {
            var currentDiv = document.getElementById("startDraggable");
        } else {
            var currentDiv = document.getElementById("draggable" + (i-1));
        }
        document.body.insertAfter(newDiv, currentDiv);
    }
}
{/* <div id="div1" ondrop="drop(event)" ondragover="allowDrop(event)"></div>
<img id="drag1" src="img_logo.gif" draggable="true" ondragstart="drag(event)" width="336" height="69"> */}
