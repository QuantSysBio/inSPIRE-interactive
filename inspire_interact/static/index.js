
async function selectUser(serverAddress, selectedUser)
// Function activated when the user is selected, showing projects available.
{
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/user/' + selectedUser,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });
    var userSelection = document.getElementById('userSelection');
    userSelection.disabled = 'disabled';
    showProjectOptions(response["message"]);
};

async function createNewUser(serverAddress)
// Function activated to create a new inSPIRE-interact user.
{
    let buttonElement = document.getElementById('createUserButton');
    buttonElement.disabled = "disabled";
    let newUser = document.getElementById('newUserInput').value;

    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/user/' + newUser,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });

    var userSelection = document.getElementById('userSelection');
    var opt = document.createElement('option');
    opt.value = newUser;
    opt.innerHTML = newUser;
    userSelection.appendChild(opt);
    userSelection.selectedIndex = userSelection.options.length-1;
    userSelection.disabled = 'disabled';

    showProjectOptions(response["message"]);
};

function showProjectOptions(options)
// Function to show the projects available for a inSPIRE user.
{
    var projectSelection = document.getElementById('projectSelection');
    var arrayLength = options.length;

    for (var i = 0; i < arrayLength; i++) {
        var opt = document.createElement('option');
        opt.value = options[i];
        opt.innerHTML = options[i];
        projectSelection.appendChild(opt);
    };
    document.getElementById("projectText").style.visibility = "visible";
    document.getElementById("projectDropDownText").style.visibility = "visible";
    document.getElementById("projectForm").style.visibility = "visible";
    document.getElementById("newProjectForm").style.visibility = "visible";
    document.getElementById("createProjectButton").style.visibility = "visible";
};

async function createNewProject(serverAddress)
// Function to create a new project.
{
    let buttonElement = document.getElementById('createProjectButton');
    buttonElement.disabled = "disabled";
    let user = document.getElementById('userSelection').value;
    let newProject = document.getElementById('newProjectInput').value;
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/project/' + user + '/' + newProject,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });

    var projectSelection = document.getElementById('projectSelection');
    var opt = document.createElement('option');
    opt.value = newProject;
    opt.innerHTML = newProject;

    projectSelection.appendChild(opt);
    projectSelection.selectedIndex = projectSelection.options.length-1;
    projectSelection.disabled = 'disabled';

    showWorkflowOptions();
};

async function selectProject(serverAddress, selectedProject)
// Function to select the project
{
    let user = document.getElementById('userSelection').value;
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/project/' + user + '/' + selectedProject,
        {
            method: 'GET',
        }
    ).then( response => {
        return response.json();
    });
    var projectSelection = document.getElementById('projectSelection');
    projectSelection.disabled = 'disabled';
    showWorkflowOptions();
};

function showWorkflowOptions()
// Function to show the workflow options to the user.
{
    document.getElementById("workflowSelectText").style.visibility = "visible";
    document.getElementById("workflowForm").style.visibility = "visible";
};


function selectWorkflow(value)
// Function to select the Interact workflow 
{
    let workflow = document.getElementById('Workflow');
    workflow.disabled = "disabled";
    let user = document.getElementById('userSelection').value;
    let project = document.getElementById('projectSelection').value;
    let message = "User <b>" + user + "</b> is working on <b>" + project + "</b> to run <b>" + value + "</b>.";
    document.getElementById("openingDiv").style.display = "none";
    document.getElementById("welcomingDiv").innerHTML = message;
    switch(value){
        case 'deleteProjectData':
            document.getElementById('executeButton').innerHTML = 'Delete All Project Data';
            document.getElementById('executeButton').style.display = 'block';
            break;
        case 'downloadProjectData':
            document.getElementById('executeButton').innerHTML = 'Download All Project Files';
            document.getElementById('executeButton').style.display = 'block';
            break;
        case 'inspireSelect':
            
            break;
        case 'inspire':
            document.getElementById("msDataDiv").style.display = "block";
            // document.getElementById("fileInstructions").style.visibility = "visible";
            // document.getElementById("fileInput").style.visibility = "visible";
            break;
    };
};

async function postFiles(serverAddress, formData, mode){
    let user = document.getElementById('userSelection').value;
    let project = document.getElementById('projectSelection').value;
    console.log(formData);
    var response = await fetch(
        'http://' + serverAddress + ':5000/interact/upload/' + user + '/' + project + '/' + mode,
        {
            method: 'POST',
            body: formData,
        }
    ).then( response => {
        return response.json();
    });
    return response;
}

async function uploadFiles(serverAddress, mode) {
    var selectedFiles = [];
    if (mode === 'proteomeSelect') {
        let hostFileElement = document.getElementById('hostProteome_file_upload');
        let pathogenFileElement = document.getElementById('pathogenProteome_file_upload');
        selectedFiles = [hostFileElement.files[0], pathogenFileElement.files[0]];
    } else {
        let fileElement = document.getElementById(mode + '_file_upload');
        console.log(fileElement);
        selectedFiles = fileElement.files;
    }
    var multiFormData = new FormData();
    for (var i = 0; i < selectedFiles.length; i++) {
        multiFormData.append('files', selectedFiles[i]);
    };
    console.log(selectedFiles);

    document.getElementById(mode + "Waiting").style.display = 'block';
    var response = await postFiles(serverAddress, multiFormData, mode);
    document.getElementById(mode + "Waiting").style.display = "none";

    console.log(response);
    updateGUI(mode);
};

/**
 * Function to asynchronously update GUI after each stage submit
 * @param {*} mode 
 */
async function updateGUI(mode) {
    switch(mode){
        case 'ms':
            document.getElementById("msDataDiv").style.display = "none";
            document.getElementById("searchDiv").style.display = "block";
            break;
        case 'search':
            document.getElementById("searchDiv").style.display = "none";
            document.getElementById("proteomeDiv").style.display = 'block';
            break;
        case 'proteome':
            document.getElementById("proteomeDiv").style.display = 'none';
            document.getElementById("parametersDiv").style.display = 'block';
            document.getElementById("executeButton").style.display = 'block';
            break;
        case 'proteomeSelect':
            document.getElementById("parametersDiv").style.display = 'block';
            document.getElementById("executeButton").style.display = 'block';
            break;
    };
}

function updateListElement(listName, arrayToAdd)
// Function to update a HTML list element with a new array.
{
    var ul = document.getElementById(listName);

    var arrayLength = arrayToAdd.length;
    for (var i = 0; i < arrayLength; i++) {
        var li = document.createElement("li");
        li.appendChild(document.createTextNode(arrayToAdd[i]));
        ul.appendChild(li);
    };
    ul.style.display = 'block';
}


async function checkFilePattern(serverAddress, file_type)
// Function to fetch all files which match a pattern specified by the user.
{
    document.getElementById(file_type + "FileList").innerHTML = "";
    let user = document.getElementById('userSelection').value;
    let project = document.getElementById('projectSelection').value;
    let filePath = document.getElementById(file_type + 'FileInput').value;

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
    updateListElement(file_type + "FileList", filesFound)
    
    document.getElementById(file_type + "FileListDiv").style.display = "block";

    switch (file_type){
        case 'ms':
            document.getElementById("searchDiv").style.display = "block";
            break;
        case 'search':
            document.getElementById("proteomeDiv").style.display = "block";
            break;
        case 'proteome':
            document.getElementById("parametersDiv").style.display = "block";
            document.getElementById("executeButton").style.display = 'block';
            break;
        case 'hostProteome':
            document.getElementById("pathogenProteomeDiv").style.display = "block";
            break;
        case 'pathogenProteome':
            document.getElementById("parametersDiv").style.display = "block";
            document.getElementById("executeButton").style.display = 'block';
            break;
    }
}

function selectSearchType(value) {
    switch(value){
        case 'searchDone':
            document.getElementById('searchEngineDiv').style.display = 'block';
            document.getElementById('searchColumn1').style.display = 'block';
            document.getElementById('searchColumn2').style.display = 'block';
            break;
        case 'msFragger':
            document.getElementById('proteomeDiv').style.display = 'block';
            break;
    };
};

function selectInspireType(value) {
    switch(value){
        case 'inspireStandard':
            document.getElementById('proteomeColumn1').style.display = 'block';
            document.getElementById('proteomeColumn2').style.display = 'block';
            // Allows for sequential viewing of both elements.
            document.getElementById('proteomeSelectColumn1').style.display = 'none';
            document.getElementById('proteomeSelectColumn2').style.display = 'none';
            break;
        case 'inspireSelect':
            document.getElementById('proteomeSelectColumn1').style.display = 'block';
            document.getElementById('proteomeSelectColumn2').style.display = 'block';
            // Allows for sequential viewing of both elements. 
            document.getElementById('proteomeColumn1').style.display = 'none';
            document.getElementById('proteomeColumn2').style.display = 'none';
            break;
    };
};

function addConfigs() {
// Function activated when a user wants to add more inSPIRE configurations.
    var tbodyRef = document.getElementById('configsTable').getElementsByTagName('tbody')[0];
    var newRow = tbodyRef.insertRow();
    for (var i = 0; i < 3; i++) {
        var newCell = newRow.insertCell();
        var newInput = document.createElement("input");
        newInput.type = "text";
        if (i === 0) {
            newInput.class = "configKey";
            newCell.appendChild(newInput);
        } else if (i === 1) {
            newInput.class = "configVale";
            newCell.appendChild(newInput);
        } else {
            var newButton = document.createElement("button");
            newButton.innerHTML = "Delete Entry";
            newButton.onclick = function() { 
                deleteRow(this);
            };
            console.log(newButton);
            newCell.appendChild(newButton);
        }
    }
};


async function executePipeline(serverAddress) {
    let user = document.getElementById('userSelection').value;
    let project = document.getElementById('projectSelection').value;
    var searchEngine = 'msfragger'
    let useMsFragger = document.getElementById('searchRequired').value;
    if (useMsFragger !== 'msFragger'){
        searchEngine = document.getElementById('searchEngineSelection').value; // TODO handle msfragger
    }
    let controlFlags = document.getElementById('controlFlagInput').value;
    var ms1Accuracy = document.getElementById('ms1AccuracyInput').value;
    var mzAccuracy = document.getElementById('ms2AccuracyInput').value;
    var mzUnits = document.getElementById('ms2UnitSelection').value;

    var configObject = {
        'user': user,
        'project': project,
        'searchEngine': searchEngine,
        'controlFlags': controlFlags,
        'ms1Accuracy': ms1Accuracy,
        'mzAccuracy': mzAccuracy,
        'mzUnits': mzUnits,
    };

    if (useMsFragger === 'msFragger'){
        configObject['runFragger'] = 1;
    } else {
        configObject['runFragger'] = 0;
    }

    var response = await postJson(serverAddress, 'inspire', configObject);

    makeDownloadVisible(response['message']);
}

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

function makeDownloadVisible(message)
// Function to provide link to the download page.
{
    if (message.startsWith('inSPIRE-Interact failed')) {
        document.getElementById("fileDownloadText").innerHTML = message;
        document.getElementById("fileDownloadText").style.display = "block";
    } else {
        document.getElementById("fileDownloadText").style.display = "block";
        var a = document.getElementById('fileDownload');
        a.href = message;
        a.innerHTML = message;
    }
};
