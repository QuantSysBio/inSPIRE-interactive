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

async function textSubmit(e, serverAddress, functionActivated) {
    if (e.keyCode !== 13){
        return
    }
    e.preventDefault();

    switch(functionActivated){
        case 'createNewUser':
            createNewUser(serverAddress)
            break;
        case 'createNewProject':
            createNewProject(serverAddress)
            break;
    };

}

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

    setElementVisibility(["project-select-div"])
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
    let workflowSelection = document.getElementById("workflow-selection");
    workflowSelection.selectedIndex = 0;
    setElementVisibility(["workflow-select-div"]);
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
        case 'deleteProjectData':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/delete/' + user + '/' + project;  
            break;
        
        case 'downloadProjectData': 
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/download/' + user + '/' + project;  
            break;
            
        case 'results':
            window.location.href = 'http://' + serverAddress + ':5000/interact/' + user + '/' + project + '/inspire'
            break;

        case 'inspire':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/usecase/' + user + '/' + project;  
            break;
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
    waitingTextElem.style.display = 'block';

    //create XHR object to send request
    var ajax = new XMLHttpRequest(
        
    );

    // add progress event to find the progress of file upload 
    ajax.upload.addEventListener("progress", progressHandler);

    // initializes a newly-created request 
    ajax.open(
        "POST",
        'http://' + serverAddress + ':5000/interact/upload/' + user + '/' + project + '/' + mode
    ); // replace with your file URL

    ajax.onreadystatechange = () => {
        // Call a function when the state changes.
        if (ajax.readyState === XMLHttpRequest.DONE && ajax.status === 200) {
            checkFilePattern(serverAddress, user, project, mode);
            waitingTextElem.style.display = "none";
        }
    };
    
    // send request to the server
    ajax.send(multiFormData);
};

function progressHandler(ev) {    
    let totalSize = Math.round((ev.total/1000000000 + Number.EPSILON) * 1000)/1000; // total size of the file in bytes
    let loadedSize = Math.round((ev.loaded/1000000000 + Number.EPSILON) * 1000)/1000; // loaded size of the file in bytes    

    document.getElementById("loaded_n_total").innerHTML = "Uploaded " + loadedSize + " GB of " + totalSize + " GB.";

    // calculate percentage 
    var percent = (ev.loaded / ev.total) * 100;
    document.getElementById("progressBar").style.display="";
    document.getElementById("progressBar").value = Math.round(percent);

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
        case 'usecase':
            window.location.href = 'http://' + serverAddress + ':5000/interact';  
            break;

        case 'ms':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/usecase/' + user + '/' + project;  
            break;

        case 'search':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/ms/' + user + '/' + project;  
            break;

        case 'proteome':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/search/' + user + '/' + project;  
            break;

        case 'parameters':
            window.location.href = 'http://' + serverAddress + ':5000/interact-page/proteome/' + user + '/' + project;  
            break;
    };

    setElementDisplay(blockIds);
    setElementDisplay(deletedIds, "none");
}

async function goHome(serverAddress) {
    window.location.href = 'http://' + serverAddress + ':5000/interact-page/home';
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
            setElementDisplay(['search-engine-div'], displayType='none');
            var configObject = {
                'user': user,
                'project': project,
                'metadata_type': 'search',
                'runFragger': 1,
                'searchEngine': 'msfragger',
            };
            postJson(serverAddress, 'metadata', configObject);
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
async function selectInspireType(value, serverAddress, user, project) {
    var configObject = {
        'user': user,
        'project': project,
        'metadata_type': 'core',
        'variant': value,
    };
    await postJson(serverAddress, 'metadata', configObject);
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
        fileDownloadTextElem.textContent = message;
    } else {   
        let a = document.getElementById('file-download');
        a.href = message;
        a.innerHTML = message;
    }

    fileDownloadTextElem.style.display = "block";
    let loadingElem = document.getElementById("loading-text");
    loadingElem.style.display = "none";
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

function controlCheck(col, file_name, item) {
    if (file_name.includes(item) & item !== '') {
        col.getElementsByClassName('infection-checkbox')[0].checked = false;
    }
};

function replicateCheck(col, file_name, item, index) {
    if (item.includes(file_name)) {
        col.getElementsByClassName('sample-value')[0].value = index + 1;
    }
};

async function parametersCheck(serverAddress, user, project)
{
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/metadata/' + user + '/' + project + '/parameters',
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });
    metaDict = response['message'];

    if ('ms1Accuracy' in metaDict) {
        document.getElementById('ms1-accuracy-input').value = metaDict['ms1Accuracy'];
    }
    if ('mzAccuracy' in metaDict) {
        document.getElementById('ms2-accuracy-input').value = metaDict['mzAccuracy'];
    }
    if ('mzUnits' in metaDict) {
        document.getElementById('ms2-unit-selection').value = metaDict['mzUnits'];
    }
    if ('runQuantification' in metaDict) {
        if (metaDict['runQuantification']){
            document.getElementById('quantification-checkbox').checked = true;
        }
    }
    if ('useBindingAffinity' in metaDict) {
        if (metaDict['useBindingAffinity'] === 'asFeature') {
            document.getElementById('panfeature').checked = true;
            document.getElementById('netmhcpan-allele-div').style.display = 'block';
        } else if (metaDict['useBindingAffinity'] === 'asValidation') {
            document.getElementById('panvalidation').checked = true;
            document.getElementById('netmhcpan-allele-div').style.display = 'block';
        }
    }
    if ('alleles' in metaDict) {
        document.getElementById('netmhcpan-allele-div').style.display = 'block';
        document.getElementById('netmhcpan-allele-input').value = metaDict['alleles'];
    }
    if ('controlFlags' in metaDict) {
        var table = document.getElementById("raw-table");
        var controlFlags = metaDict['controlFlags'].split(",");
        for (var row_idx = 1, row; row = table.rows[row_idx]; row_idx++) {
            file_name = row.cells[0].textContent;
            col = row.cells[2];
            if (typeof col !== "undefined") {
                col.getElementsByClassName('infection-checkbox')[0].checked = true;
                controlFlags.forEach(function (item, _) {
                    controlCheck(col, file_name, item)
                });
            };
        }
    }
    if ('technicalReplicates' in metaDict) {
        var table = document.getElementById("raw-table");
        for (var row_idx = 1, row; row = table.rows[row_idx]; row_idx++) {
            file_name = row.cells[0].textContent;
            col = row.cells[1];
            metaDict['technicalReplicates'].forEach(function (item, index) {
                replicateCheck(col, file_name, item, index)
            });
        }
    }
    if ('additionalConfigs' in metaDict) {
        for (const configKey in metaDict['additionalConfigs']) {
            var table = document.getElementById('configs-table');
            var lastRow = table.rows[ table.rows.length - 1 ];
            lastRow.cells[0].getElementsByClassName('config-key')[0].value = configKey
            lastRow.cells[1].getElementsByClassName('config-value')[0].value = metaDict['additionalConfigs'][configKey];
            addConfigs();
          };
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
async function cancelPipeline(serverAddress, user, project) {
    var configObject = {
        'user': user,
        'project': project,
    };

    if (confirm("Are you sure you want to delete the project " + project + "?") == true) {
        var response = await postJson(serverAddress, 'cancel', configObject);
        let cancelElem = document.getElementById("cancelled-text")
        cancelElem.innerHTML = response['message'];
    } else {
        let cancelElem = document.getElementById("cancelled-text")
        cancelElem.innerHTML = 'No cancellation.';
    }
};

async function cancelJobById(serverAddress) {
    var configObject = {
        'jobID': document.getElementById('cancel-job-input').value,
    };
    if (confirm("Are you sure you want to cancel execution for job ID " + configObject['jobID'] + "?") == true) {
        var response = await postJson(serverAddress, 'cancel', configObject);
        let cancelElem = document.getElementById("cancel-text")
        cancelElem.innerHTML = response['message'];
    } else {
        let cancelElem = document.getElementById("cancel-text")
        cancelElem.innerHTML = 'No cancellation.';
    }
};

async function downloadOutputs(serverAddress, user, project) {
    var configObject = {
        'user': user,
        'project': project,
    };
    let downloadElem = document.getElementById("download-text");
    downloadElem.innerHTML = 'There may be some delay before your download begins in order to zip the output folder.';
    await postJson(serverAddress, 'download', configObject)
};


async function deleteProject(serverAddress, user, project) {
    var configObject = {
        'user': user,
        'project': project,
    };

    if (confirm("Are you sure you want to delete the project " + project + "?") == true) {
        await postJson(serverAddress, 'cancel', configObject)
        var response = await postJson(serverAddress, 'delete', configObject);
        let deleteElem = document.getElementById("delete-text");
        deleteElem.innerHTML = response['message'];
    } else {
        let deleteElem = document.getElementById("delete-text");
        deleteElem.innerHTML = 'No deletion.';
    } 
};

function constructConfigObject(user, project) {
    let ms1Accuracy = document.getElementById('ms1-accuracy-input').value;
    let mzAccuracy = document.getElementById('ms2-accuracy-input').value;
    let mzUnits = document.getElementById('ms2-unit-selection').value;


    var table = document.getElementById("raw-table");
    var file_name = "";
    var technicalReplicates = Object();
    var controlFlags = "";
    for (var row_idx = 1, row; row = table.rows[row_idx]; row_idx++) {
        for (var col_idx = 0, col; col = row.cells[col_idx]; col_idx++) {
            if (col_idx === 0){
                file_name = col.textContent;
            }
            if (col_idx === 1){
                sample_value = col.getElementsByClassName('sample-value')[0].value;
                if (sample_value in technicalReplicates){
                    technicalReplicates[sample_value].push(file_name);
                } else {
                    technicalReplicates[sample_value] = [file_name];
                }
            }
            if (col_idx === 2){
                if (col.getElementsByClassName('infection-checkbox')[0].checked) {
                    continue
                } else {
                    controlFlags += file_name;
                    controlFlags += ",";
                }
            }
        }  
    }

    var configObject = {
        'user': user,
        'project': project,
        'ms1Accuracy': ms1Accuracy,
        'mzAccuracy': mzAccuracy,
        'mzUnits': mzUnits,
        'controlFlags': controlFlags,
        'technicalReplicates': Object.values(technicalReplicates)
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

    configObject['runQuantification'] = (
        document.getElementById('quantification-checkbox'
    ).checked) ? 1 : 0;
    configObject['additionalConfigs'] = additionalConfigs;
    return configObject;
}

async function executePipeline(serverAddress, user, project) {

    let paramSaveElem = document.getElementById("params-save-text");
    paramSaveElem.style.display = "none";
    document.getElementById('execute-button').disabled = "disabled";
    
    let loadingElem = document.getElementById("loading-text");
    loadingElem.style.display = "block";

    var configObject = constructConfigObject(user, project);

    var response = await postJson(serverAddress, 'inspire', configObject);

    configObject['metadata_type'] = 'parameters';
    postJson(serverAddress, 'metadata', configObject);

    makeDownloadVisible(response['message']);

};


async function saveParameters(serverAddress, user, project) {
    let paramSaveElem = document.getElementById("params-save-text");
    paramSaveElem.style.display = "block";

    configObject = constructConfigObject(user, project);
    configObject['metadata_type'] = 'parameters';
    
    await postJson(serverAddress, 'metadata', configObject);
};


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
    }  else {
        setElementDisplay(['netmhcpan-allele-div'], 'none');
    }
}

/**
 * Adds additional GUI elements for further inSPIRE configurations.
 */
function addConfigs() {
        let newRow = document.getElementById('configs-table').getElementsByTagName('tbody')[0].insertRow();

        let newButton = document.createElement("input");
        newButton.type = "button";
        newButton.value = "Delete Entry";
        newButton.onclick = function() { 
            deleteRow(this);
        };

        const CLASSES = ['config-key', 'config-value']

        for (var i = 0; i < 3; i++) {
            let newCell = newRow.insertCell();
            let newInput = document.createElement("input");
            newInput.type = "text";

            if (i == 2) {
                // ms-data-extra
                newButton.classList.add('ms-data-extra');
                newCell.appendChild(newButton);
            } else {
                newInput.classList.add(CLASSES[i]);
                newCell.appendChild(newInput);
            }
        }
    };