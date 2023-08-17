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
function selectWorkflow(value, serverAddress) {
    let user = document.getElementById('user-selection').value;
    let project = document.getElementById('project-selection').value;

    switch(value){
        case 'deleteProjectData': case 'downloadProjectData': {
            let executeButtonElmt = document.getElementById('execute-button');

            executeButtonElmt.innerHTML = (value == 'deleteProjectData') ? 'Delete All Project Data' : 'Download All Project Files';
            executeButtonElmt.style.display = 'block';
        } break;
            
        case 'results': {
            window.location.href = 'http://' + serverAddress + ':5000/interact/' + user + '/' + project + '/inspire'
         } break;

        case 'inspire':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/usecase/' + user + '/' + project;  

            // let message = "User <b>" + user + "</b> is working on <b>" + project + "</b> to run <b>" + value + "</b>.";

            // document.getElementById("opening-div").style.display = "none";
            // document.getElementById("welcoming-div").innerHTML = message;
            // cycleButtonVisibility("back");
            // cycleButtonVisibility("forward");

            // document.getElementById("ms-data-div").style.display = "block";
            // checkFilePattern(serverAddress, 'ms');
            // break;
    };
};

/* ============================================= FUNCTIONAL ============================================= */

async function uploadFiles(serverAddress, user, project, mode) {
    var selectedFiles = (mode === 'proteome-select') ? [
            document.getElementById('host-proteome-file-upload').files[0], 
            document.getElementById('pathogen-proteome-file-upload').files[0]
        ] 
        : Array.from(document.getElementById(mode + '-file-upload').files);

    //If file upload was not completed, do not allow users to proceed.
    if(!checkPreconditions(mode, selectedFiles)) return;

    var multiFormData = new FormData();
    selectedFiles.forEach ((elem) => {
        multiFormData.append('files', elem )
    });

    let waitingTextElem = document.getElementById(mode + "-waiting");
    
    //Displays the waiting text during the postFiles process, removing it right after.
    waitingTextElem.style.display = 'block';
    console.log(await postFiles(serverAddress, user, project, multiFormData, mode));
    checkFilePattern(serverAddress, user, project, mode);
    waitingTextElem.style.display = "none";
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
async function checkFilePattern(serverAddress, user, project, file_type) {
    console.log(file_type);
    document.getElementById(file_type + "-file-list").innerHTML = "";

    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/checkPattern/' + file_type,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({'user': user, 'project': project})
        }
    ).then( response => {
        return response.json();
    });

    var filesFound = response['message'];
    updateListElement(file_type + "-file-list", filesFound);

    if (file_type === 'search') {
        var response = await fetch(
            'http://' + serverAddress + ':5000/interact/metadata/' + user + '/' + project + '/' + file_type,
            {
                method: 'GET',
            }
        ).then( response => {
            return response.json();
        });
        metaDict = response['message'];
        if (Object.keys(metaDict).length !== 0) {
            if (metaDict['runFragger'] == 1) {
                document.getElementById('search-required-selection').value = 'searchNeeded';
                selectSearchType('searchNeeded', serverAddress, user, project)
            } else {
                selectSearchType('searchDone', serverAddress, user, project)
                document.getElementById('search-required-selection').value = 'searchDone';
                if ('searchEngine' in metaDict){
                    document.getElementById('search-engine-selection').value = metaDict['searchEngine'];
                    selectSearchEngine(metaDict['searchEngine'], serverAddress, user, project)
                }
            }
        }
    };
}

/**
 * Clear all files which match a user-specified pattern.
 * 
 * @param {*} serverAddress 
 * @param {*} file_type 
 */
async function clearFilePattern(serverAddress, user, project, file_type) {
    document.getElementById(file_type + "-file-list").innerHTML = "";


    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/clearPattern/' + file_type,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({'user': user, 'project': project})
        }
    ).then( response => {
        return response.json();
    });

    var filesFound = response['message'];
    updateListElement(file_type + "-file-list", filesFound)
}


/* ============================================= GUI FUNCTIONS ============================================= */

var lastFrame = "init";
/**
 * Function to asynchronously update GUI after each stage submit.
 * 
 * @param {*} currentFrame frame currently being cycled out of.
 */
async function updateGUI(currentFrame, serverAddress) {
    let blockIds;
    let deletedIds;

    switch(currentFrame){
        case 'ms':
            checkFilePattern(serverAddress, 'search');
            deletedIds = ["ms-data-div"];
            blockIds = ["search-div"];
            break;

        case 'search':
            deletedIds = ["search-div"];
            blockIds = ["proteome-div"];
            break;

        case 'proteome':
            presentFrame = "configs";
            deletedIds = ["proteome-div"];
            blockIds = ["parameters-div", "execute-button"];
            document.getElementById("forward-button").style.display = 'none';
            break;
        
        case 'proteome-select':
            presentFrame = "configs";
            deletedIds = ["proteome-div"];
            blockIds = ["parameters-div", "execute-button"];
            document.getElementById("forward-button").style.display = 'none';
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
async function revertGUI(serverAddress, user, project, frame) {
    var blockIds = [];
    let deletedIds;

    switch(frame) {            
        case 'ms':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/usecase';  
            break;

        case 'search':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/ms/' + user + '/' + project;  
            break;
        
        case 'usecase':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/search/' + user + '/' + project;  
            break;

        case 'proteome':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/usecase/' + user + '/' + project;  
            break;

        case 'parameters':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/proteome/' + user + '/' + project;  
            break;
    };

    setElementDisplay(blockIds);
    setElementDisplay(deletedIds, "none");
}

async function forwardGUI(serverAddress, user, project, frame) {
    switch(frame) {
        case 'usecase':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/ms/' + user + '/' + project;  
            break;
        case 'ms':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/search/' + user + '/' + project;  
            break;
        case 'search':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/proteome/' + user + '/' + project;  
            break;
        case 'proteome':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/parameters/' + user + '/' + project;  
            break;
    };

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
        var li = document.createElement("li");
        li.appendChild(document.createTextNode(elem));
        ul.appendChild(li);
    });

    ul.style.display = 'block';
}


/**
 * Sets the search type according to the user's choice, additionally updating the GUI to reflect the choice.
 * 
 * @param {*} value chosen search type.
 */
function selectSearchType(value, serverAddress, user, project) {
    switch(value){
        case 'searchDone':
            setElementDisplay(['search-engine-div']);
            break;
        case 'searchNeeded':
            var configObject = {
                'user': user,
                'project': project,
                'metadata_type': 'search',
                'runFragger': 1,
                'searchEngine': 'msfragger',
            };
            postJson(serverAddress, 'metadata', configObject);
            forwardGUI(serverAddress, user, project, 'search');
            break;
    };
};

function selectSearchEngine(value, serverAddress, user, project) {
    var configObject = {
        'user': user,
        'project': project,
        'metadata_type': 'search',
        'runFragger': 0,
        'searchEngine': value,
    };
    postJson(serverAddress, 'metadata', configObject);
    setElementDisplay([ 'search-column-1', 'search-column-2', 'search-separator']);
};

/**
 * Sets the inspire type according to the user's choice, additionally updating the GUI to reflect the choice.
 * 
 * @param {*} value chosen inspire type.
 */
function selectInspireType(value, serverAddress, user, project) {
    var configObject = {
        'user': user,
        'project': project,
        'metadata_type': 'core',
        'variant': value,
    };
    postJson(serverAddress, 'metadata', configObject);
    forwardGUI(serverAddress, user, project, 'usecase');
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
function cycleButtonVisibility(buttonType) {
    let button = document.getElementById(buttonType+"-button")

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
async function postFiles(serverAddress, user, project, formData, mode){
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

async function parametersCheck(serverAddress, user, project)
{
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/metadata/' + user + '/' + project + '/core',
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });
    metaDict = response['message'];
    if (metaDict['variant'] === 'select') {
        let controlFlagDiv = document.getElementById('control-flag-div');
        controlFlagDiv.style.display = 'block';
    }
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
async function executePipeline(serverAddress, user, project) {
    let ms1Accuracy = document.getElementById('ms1-accuracy-input').value;
    let mzAccuracy = document.getElementById('ms2-accuracy-input').value;
    let mzUnits = document.getElementById('ms2-unit-selection').value;
    let controlFlags = document.getElementById('control-flag-input').value;

    var configObject = {
        'user': user,
        'project': project,
        'ms1Accuracy': ms1Accuracy,
        'mzAccuracy': mzAccuracy,
        'mzUnits': mzUnits,
        'controlFlags': controlFlags,
    };


    if (document.getElementById('panfeature').checked){
        configObject['useBindingAffinity'] = 'asFeature';
        configObject['alleles'] =  document.getElementById('netmhcpan-allele-input').value;
    } else if (document.getElementById('panvalidation').checked) {
        configObject['useBindingAffinity'] = 'asValidation';
        configObject['alleles'] =  document.getElementById('netmhcpan-allele-input').value;
    };

    //gets rows of table
    var configTable = document.getElementById('configs-table');
    var rowLength = configTable.rows.length;


    var additionalConfigs = {};
    //loops through rows    
    for (i = 1; i < rowLength; i++){
        //gets cells of current row
        var configCells = configTable.rows.item(i).cells;
        var configKey = configCells[0].children[0].value;
        var configValue = configCells[1].children[0].value;
        if (configKey){
            additionalConfigs[configKey] = configValue;
        }
    }
    console.log(additionalConfigs)

    configObject['runQuantification'] = (
        document.getElementById('quantification'
    ).checked) ? 1 : 0;
    configObject['additionalConfigs'] = additionalConfigs;
    
    var response = await postJson(serverAddress, 'inspire', configObject);

    makeDownloadVisible(response['message']);
}

function deleteRow(r)
// Function to delete a row from the table.
{
    var i = r.parentNode.parentNode.rowIndex;
    document.getElementById("configs-table").deleteRow(i);
};

function competingCheckboxes(checkbox, checkboxClass)
// 
{
    if (checkbox.checked){
        Array.from(
            document.getElementsByClassName(checkboxClass)
        ).forEach((box) => {
            box.checked = false;
        });
        checkbox.checked = true;
        setElementDisplay(['netmhcpan-allele-div']);
    }
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
                newCell.appendChild(newButton);
            } else {
                newInput.class = CLASSES[i];
                newCell.appendChild(newInput);
            }
        }
    };