/**
 * 
 * 
 * @author {John A. Cormican}
 * @author {Manuel Santos Pereira}
 */


/* ============================================= USER ============================================= */

/**
 * Sets a user selected through HTML, forcing a GUI update to show the user's projects.
 * 
 * @param {*} serverAddress address of the server hosting inSPIRE-interact.
 * @param {*} selectedUser user selected by user.
 */
async function selectUser(serverAddress, selectedUser) {
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/user/' + selectedUser,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });

    showProjectOptions(response["message"]);
};

/**
 * Creates a new inSPIRE-interact user, forcing a GUI update to show the user's projects.
 * 
 * @param {*} serverAddress address of the server hosting inSPIRE-interact.
 */
async function createNewUser(serverAddress) {
    //Disable the create user button.
    document.getElementById('create-user-button').disabled = "disabled";
    
    let newUser = document.getElementById('new-user-input').value;

    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/user/' + newUser,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });

    let opt = document.createElement('option');
    opt.value = newUser;
    opt.innerHTML = newUser;

    let userSelection = document.getElementById('user-selection');
    userSelection.appendChild(opt);
    userSelection.selectedIndex = userSelection.options.length-1;


    showProjectOptions(response["message"]);
};


/* ============================================= PROJECT ============================================= */

/**
 * Updates GUI to display the selected user's projects.
 * 
 * @param {*} options the multiple projects belonging to the selected user.
 */
function showProjectOptions(options) {
    let projectSelection = document.getElementById("project-selection");

    resetSelect(projectSelection);

    options.forEach ((option) => {
        let optionElem = document.createElement('option');
        optionElem.value = option;
        optionElem.innerHTML = option;

        projectSelection.appendChild(optionElem);
    });

    setElementVisibility(["project-select-div", "opening-Vl-1"])
};

/**
 * Resets the project selections displayed in the drop-down menu in case the user is re-selected.
 * 
 * @param {HTMLElement} element drop-down menu element containing the projects.
 */
function resetSelect(element) {
    while(element.lastChild.className != "default")
        element.lastChild.remove()
    
    element.selectedIndex = 0;
}

/**
 * Creates a new project for the chosen user, calls the backend services and updates the GUI to reflect the addition.
 * 
 * @param {*} serverAddress  address of the server hosting inSPIRE-interact.
 */
async function createNewProject(serverAddress) {
    //Disable the create project button.
    document.getElementById('create-project-button').disabled = "disabled";


    let user = document.getElementById('user-selection').value;
    let newProject = document.getElementById('new-project-input').value;
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/project/' + user + '/' + newProject,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });

    let opt = document.createElement('option');
    opt.value = newProject;
    opt.innerHTML = newProject;

    let projectSelection = document.getElementById('project-selection');
    projectSelection.appendChild(opt);
    projectSelection.selectedIndex = projectSelection.options.length-1;

    showWorkflowOptions();
};

/**
 * Sets a selected project, getting selection from backend.
 * 
 * @param {*} serverAddress address of the server hosting inSPIRE-interact. 
 * @param {*} selectedProject project selected by the user.
 */
async function selectProject(serverAddress, selectedProject) {
    let user = document.getElementById('user-selection').value;
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/project/' + user + '/' + selectedProject,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });
   
   
    showWorkflowOptions();
};


/* ============================================= WORKFLOW ============================================= */

/**
 * Updates GUI to display available workflow options.
 */
function showWorkflowOptions() {
    setElementVisibility(["workflow-select-div", "opening-Vl-2"]);
};


/**
 * Sets the selected interact workflow, updating the GUI to reflect the choice.
 * 
 * @param {*} value user's choice of workflow. 
 */
function selectWorkflow(value) {
    let user = document.getElementById('user-selection').value;
    let project = document.getElementById('project-selection').value;
    let message = "User <b>" + user + "</b> is working on <b>" + project + "</b> to run <b>" + value + "</b>.";

    document.getElementById("opening-div").style.display = "none";
    document.getElementById("welcoming-div").innerHTML = message;
    cycleBackButtonVisibility();

    switch(value){
        case 'deleteProjectData': case 'downloadProjectData': {
            let executeButtonElmt = document.getElementById('execute-button');

            executeButtonElmt.innerHTML = (value == 'deleteProjectData') ? 'Delete All Project Data' : 'Download All Project Files';
            executeButtonElmt.style.display = 'block';
        } break;
            
        case 'inspireSelect':
            break;

        case 'inspire':
            document.getElementById("ms-data-div").style.display = "block";
            break;
    };
};

/* ============================================= FUNCTIONAL ============================================= */

async function uploadFiles(serverAddress, mode) {
    var selectedFiles = (mode === 'proteome-select') ? [
            document.getElementById('host-proteome-file-upload').files[0], 
            document.getElementById('pathogen-proteome-file-upload').files[0]
        ] 
        : Array.from(document.getElementById(mode + '-file-upload').files);

    console.log(selectedFiles)

    //If file upload was not completed, do not allow users to proceed.
    if(!checkPreconditions(mode, selectedFiles)) return;

    var multiFormData = new FormData();
    selectedFiles.forEach ((elem) => {
        multiFormData.append('files', elem )
    });

    let waitingTextElem = document.getElementById(mode + "-waiting");
    
    //Displays the waiting text during the postFiles process, removing it right after.
    waitingTextElem.style.display = 'block';
    console.log(await postFiles(serverAddress, multiFormData, mode));
    waitingTextElem.style.display = "none";

    updateGUI(mode);
};

function checkPreconditions(mode, files) {
    let noFilesText = document.getElementById(mode + "-no-files");

    if(files.length == 0 || (mode == "proteome-select" && (typeof files[0] == "undefined" || typeof files[1] == "undefined"))) {
        noFilesText.style.display = "block";
        return false;
    }

    noFilesText.style.display = "none";
    return true;
}

/**
 * Fetches all files which match a user-specified pattern.
 * 
 * @param {*} serverAddress 
 * @param {*} file_type 
 */
async function checkFilePattern(serverAddress, file_type) {
    document.getElementById(file_type + "-file-list").innerHTML = "";

    let user = document.getElementById('user-selection').value;
    let project = document.getElementById('project-selection').value;
    let filePath = document.getElementById(file_type + '-file-input').value;

    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/checkPattern/' + file_type,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({'user': user, 'project': project, 'filePattern': filePath})
        }
    ).then( response => {
        return response.json();
    });

    var filesFound = response['message'];
    updateListElement(file_type + "-file-list", filesFound)

    let blockIds = [file_type + "-file-list-div"]

    switch (file_type){
        case 'ms':
            blockIds.push("search-div")
            break;
        case 'search':
            blockIds.push("proteome-div");
            break;
        case 'proteome': case 'pathogen-proteome':
            blockIds.push("parameters-div");
            blockIds.push("execute-button");
            break;
        case 'host-proteome':
            blockIds.push("pathogen-proteome-div");
            break;
    }

    setElementDisplay(blockIds)
}


/* ============================================= GUI FUNCTIONS ============================================= */

var lastFrame = "init";
/**
 * Function to asynchronously update GUI after each stage submit.
 * 
 * @param {*} currentFrame frame currently being cycled out of.
 */
async function updateGUI(currentFrame) {
    let blockIds;
    let deletedIds;

    switch(currentFrame){
        case 'ms':
            deletedIds = ["ms-data-div"];
            blockIds = ["search-div"];
            break;

        case 'search':
            deletedIds = ["search-div"];
            blockIds = ["proteome-div"];
            break;

        case 'proteome': case 'proteome-select':
            deletedIds = ["proteome-div"];
            blockIds = ["parameters-div", "execute-button"];
            break;
    };
    
    setElementDisplay(blockIds);
    setElementDisplay(deletedIds, "none");
    lastFrame = currentFrame;
}

/**
 * Function to revert the GUI to the previous frame.
 * 
 * @param {*} frame frame to be reverted to.
 */
async function revertGUI(frame = lastFrame) {
    var blockIds = [];
    let deletedIds;

    switch(frame) {
        case "init" :
            document.getElementById("opening-div").style.display = "flex";
            deletedIds = ["welcoming-div", "ms-data-div"]
            document.getElementById('workflow-selection').selectedIndex = 0;
            cycleBackButtonVisibility();
            break;
            
        case 'ms':
            blockIds = ["ms-data-div"];
            deletedIds = ["search-div"];
            lastFrame = "init"
            break;

        case 'search':
            blockIds = ["search-div"];
            deletedIds = ["proteome-div"];
            lastFrame = "ms"
            break;

        case 'proteome': case 'proteome-select':
            blockIds = ["proteome-div"];
            deletedIds = ["parameters-div", "execute-button"]; 
            lastFrame = "search"
            break;
    };

    setElementDisplay(blockIds);
    setElementDisplay(deletedIds, "none");
}

/**
 * Sets the display of elements with the given ids to the desired displayType.
 * 
 * Defaults to 'block' display.
 * 
 * @param {*} ids ids of elements to affect.
 * @param {*} displayType style type to apply to the desired elements.
 */
function setElementDisplay(ids, displayType = 'block') {
    ids.forEach((id) => {
        document.getElementById(id).style.display = displayType;
    });
}

/**
 * Sets the visibility of elements with the given ids to the desired visibilityType.
 * 
 * Defaults to 'visible' visibility.
 * 
 * @param {*} ids ids of elements to affect.
 * @param {*} visibilityType style type to apply to the desired elements.
 */
function setElementVisibility(ids, visibilityType = 'visible') {
    ids.forEach((id) => {
        document.getElementById(id).style.visibility = visibilityType;
    });
}

/**
 * Updates an HTML list element with an array's elements.
 * 
 * @param {*} listName id of the already-existing list.
 * @param {*} array array to add.
 */
function updateListElement(listName, array) {
    let ul = document.getElementById(listName);

    array.forEach ((elem) => {
        ul.appendChild(
            document.createElement("li").appendChild(document.createTextNode(elem))
        );
    });

    ul.style.display = 'block';
}


/**
 * Sets the search type according to the user's choice, additionally updating the GUI to reflect the choice.
 * 
 * @param {*} value chosen search type.
 */
function selectSearchType(value) {
    let blockIds;

    switch(value){
        case 'searchDone':
            blockIds = ['search-engine-div', 'search-column-1', 'search-column-2']
            break;
        case 'searchNeeded':
            blockIds = ['proteome-div'];
            updateGUI('search')
            break;
    };

    setElementDisplay(blockIds)
};

/**
 * Sets the inspire type according to the user's choice, additionally updating the GUI to reflect the choice.
 * 
 * @param {*} value chosen inspire type.
 */
function selectInspireType(value) {
    let flexIds;
    let noneIds;

    switch(value){
        case 'inspireStandard':
            blockIds = ["sub-proteome-div"];
            noneIds = ["sub-proteome-select-div"]
            break;
        case 'inspireSelect':
            blockIds = ["sub-proteome-select-div"]
            noneIds = ["sub-proteome-div"];
            break;
    };

    setElementDisplay(blockIds, "flex");
    setElementDisplay(noneIds, 'none');
};

/**
 * Provides the link to the download page.
 * 
 * @param {*} message server response to request. 
 */
function makeDownloadVisible(message) {
    let fileDownloadTextElem = document.getElementById("file-download-text")

    if (message.startsWith('inSPIRE-Interact failed')) {
        fileDownloadTextElem.innerHTML = message;
    } else {   
        let a = document.getElementById('file-download');
        a.href = message;
        a.innerHTML = message;
    }

    fileDownloadTextElem.style.display = "block";
};

/**
 * Cycles the back button's visibility from visible to hidden and vice-versa.
 */
function cycleBackButtonVisibility() {
    let button = document.getElementById("back-button")

    button.style.visibility = (button.style.visibility == "visible") ? "hidden" : "visible"
}

/* ============================================= BACKEND ============================================= */

/**
 * Posts the selected files to the backend.
 * 
 * @param {*} serverAddress  address of the server hosting inSPIRE-interact. 
 * @param {*} formData 
 * @param {*} mode 
 * @returns 
 */
async function postFiles(serverAddress, formData, mode){
    console.log("Form data: " + formData);

    let user = document.getElementById('user-selection').value;
    let project = document.getElementById('project-selection').value;
    return await fetch(
        'http://' + serverAddress + ':5000/interact/upload/' + user + '/' + project + '/' + mode,
        {
            method: 'POST',
            body: formData,
        }
    ).then( response => {
        return response.json();
    });
}

/**
 * POSTs JSON data to an Interact endpoint.
 * 
 * @param {*} serverAddress  address of the server hosting inSPIRE-interact. 
 * @param {*} endPoint endpoint to POST to.
 * @param {*} configObject 
 * @returns reponse of the endpoint to the POST request.
 */
async function postJson(serverAddress, endPoint, configObject)
// Function to POST json data to a Interact endpoint.
{
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/' + endPoint,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(
                configObject
            )
        },
    ).then( response => {
        return response.json();
    });

    return response;
}

/**
 * Executes the base inSPIRE pipeline at the end of the user-led setup.
 * 
 * @param {*} serverAddress address of the server hosting inSPIRE-interact.
 */
async function executePipeline(serverAddress) {
    let user = document.getElementById('user-selection').value;
    let project = document.getElementById('project-selection').value;
    let useMsFragger = document.getElementById('search-required').value;
    let searchEngine = (useMsFragger != 'searchNeeded') ? document.getElementById('search-engine-selection').value : 'msfragger'; 
    let controlFlags = document.getElementById('control-flag-input').value;
    let ms1Accuracy = document.getElementById('ms1-accuracy-input').value;
    let mzAccuracy = document.getElementById('ms2-accuracy-input').value;
    let mzUnits = document.getElementById('ms2-unit-selection').value;

    var configObject = {
        'user': user,
        'project': project,
        'searchEngine': searchEngine,
        'controlFlags': controlFlags,
        'ms1Accuracy': ms1Accuracy,
        'mzAccuracy': mzAccuracy,
        'mzUnits': mzUnits,
    };

    configObject['runFragger'] = (useMsFragger == 'searchNeeded') ? 1 : 0;
    
    var response = await postJson(serverAddress, 'inspire', configObject);

    makeDownloadVisible(response['message']);
}

/**
 * Adds additional GUI elements for further inSPIRE configurations.
 */
function addConfigs() {
        let newRow = document.getElementById('configs-table').getElementsByTagName('tbody')[0].insertRow();

        let newButton = document.createElement("button");
        newButton.innerHTML = "Delete Entry";
        newButton.onclick = function() { 
            deleteRow(this);
        };

        const CLASSES = ['config-key', 'config-value']

        for (var i = 0; i < 3; i++) {
            let newCell = newRow.insertCell();
            let newInput = document.createElement("input");
            newInput.type = "text";

            if (i == 2) {
                console.log(newButton);
                newCell.appendChild(newButton);
            } else {
                newInput.class = CLASSES[i];
                newCell.appendChild(newInput);
            }
        }
    };