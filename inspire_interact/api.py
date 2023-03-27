""" Main api routes for inSPIRE-interactive
"""
from argparse import ArgumentParser
import os
import socket

import flask
from flask import request, Response, render_template, send_from_directory, abort
from flask.json import jsonify
from flask_cors import cross_origin
import yaml

from inspire_interact.constants import (
    ALL_CONFIG_KEYS,
    FILESERVER_NAME_KEY,
    FRAGGER_MEMORY_KEY,
    FRAGGER_PATH_KEY,
    INTERACT_HOME_KEY,
    INTERMEDIATE_FILES,
    MODE_KEY,
    SERVER_ADDRESS_KEY,
)
from inspire_interact.utils import check_pids, prepare_inspire

app = flask.Flask(__name__, template_folder='templates')

@app.route('/favicon.ico')
@cross_origin()
def favicon():
    """ Endpoint sending the inSPIRE favicon.
    """
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )

@app.route('/static/<path:path>')
@cross_origin()
def send_static(path):
    """ Function to send static files from the static folder.
    """

    return send_from_directory('static', path)

@app.route('/interact/user/<user>', methods=['GET'])
@cross_origin()
def get_user(user):
    """ Function to check for existing user or create a new user folder.
    """  
    projects = os.listdir(f'projects/{user}')
    projects = [project for project in projects if not project.endswith('.tar')]
   
    return jsonify(message=projects)

@app.route('/interact/user/<user>', methods=['PUT'])
@cross_origin()
def put_user(user):
    if(os.path.isdir(f'{app.config[INTERACT_HOME_KEY]}/projects/{user}')):
        abort(405, description="Resource already exists.")
    
    os.mkdir(f'projects/{user}')
    projects = []
            
    return jsonify(message = projects)

@app.errorhandler(405)
@cross_origin()
def resource_not_accessible(e):
    return jsonify(error=(str(e))), 405

@app.route('/interact/project/<user>/<project>', methods=['GET'])
@cross_origin()
def create_project(user, project):
    """ Function to create a new user project.
    """
    if not os.path.isdir(f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}'):
        os.mkdir(f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}')
    return jsonify(message='Ok')

@app.route('/interact/upload/<user>/<project>/<file_type>', methods=['POST'])
@cross_origin()
def upload_file(user, project, file_type):
    """ Function to create a new user project.
    """
    home_key= app.config[INTERACT_HOME_KEY]
    upload_home = f'{home_key}/projects/{user}/{project}/{file_type}'

    if not os.path.isdir(f'{home_key}/projects/{user}/{project}/{file_type}'):
        os.mkdir(f'projects/{user}/{project}/{file_type}')

    uploaded_files = request.files.getlist("files")

    if file_type == 'proteome':
        uploaded_files[0].save(
            f'{upload_home}/proteome.fasta'
        )
    elif file_type == 'proteomeSelect':
        uploaded_files[0].save(
            f'{upload_home}/hostProteome.fasta'
        )
        uploaded_files[1].save(
            f'{upload_home}/pathogenProteome.fasta'
        )
        with open(f'{upload_home}/proteome.fasta', 'w', encoding='UTF-8') as total_file:
            for prot_type in ['host', 'pathogen']:
                with open(
                    f'{upload_home}/{prot_type}Proteome.fasta',
                    mode='r',
                    encoding='UTF-8',
                ) as source_file:
                    for line in source_file:
                        total_file.write(line)
    else:
        for u_file in uploaded_files:
            u_file.save(
                f'{upload_home}/{u_file.filename}'
            )

    return jsonify(message='Ok')

@app.route('/interact/checkPattern/<file_type>', methods=['POST'])
@cross_origin()
def check_file_pattern(file_type):
    """ Function for checking which files match a particular file pattern provided.
    """
    config_data = request.json
    user = config_data['user']
    project = config_data['project']
    file_pattern = config_data['filePattern']

    if file_pattern.startswith('FILESERVER:') and app.config[FILESERVER_NAME_KEY] is None:
        return jsonify(
            message=['Error: A file server name has not been passed to inSPIRE-Interact.']
        )

    if os.path.exists(
        f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}/{file_type}_file_list.txt'
    ):
        os.remove(f'projects/{user}/{project}/{file_type}_file_list.txt')

    if file_pattern.startswith('FILESERVER:'):
        fetch_matched_files = (
            f"ssh {app.config[FILESERVER_NAME_KEY]} 'ls -al {file_pattern}' | "+
            f" cat >> projects/{user}/{project}/{file_type}_file_list.txt"
        )
    else:
        fetch_matched_files = (
            f"ls -al {file_pattern} >> projects/{user}/{project}/{file_type}_file_list.txt"
        )

    os.system(fetch_matched_files)

    with open(
        f'projects/{user}/{project}/{file_type}_file_list.txt', mode='r', encoding='UTF-8'
    ) as list_file:
        file_list = list_file.readlines()
        all_files = [x.split()[-1].split('\n')[0] for x in file_list]

    return jsonify(message=all_files)

@app.route('/interact', methods=['GET'])
@cross_origin()
def interact_home():
    """ Endpoint serving the inspire_interactive Home Page.
    """
    usernames = os.listdir(f'{app.config[INTERACT_HOME_KEY]}/projects')
    option_list = [
        f'<option value="{username}">{username}</option>' for username in usernames
    ]
    options_html = ' '.join(option_list)
    return render_template(
        'index.html',
        server_address=app.config[SERVER_ADDRESS_KEY],
        user_list=options_html,
        mode=app.config[MODE_KEY],
    )

@app.route('/interact/inspire', methods=['POST'])
@cross_origin()
def run_inspire_core():
    """ Run the inSPIRE core pipeline.
    """
    try:
        config_dict = request.json
        print(config_dict)
        user = config_dict['user']
        project_title = config_dict['project']
        server_address = app.config[SERVER_ADDRESS_KEY]
        home_key= app.config[INTERACT_HOME_KEY]
        fragger_path = app.config[FRAGGER_PATH_KEY]
        fragger_memory = app.config[FRAGGER_MEMORY_KEY]
        project_home = f'{home_key}/projects/{user}/{project_title}'

        inspire_settings = prepare_inspire(config_dict, project_home, fragger_path, fragger_memory)

        with open(
            f'projects/{user}/{project_title}/inspire_script.sh',
            'w',
            encoding='UTF-8'
        ) as bash_file:
            bash_file.write(
                f'echo $$ > {project_home}/inspire_pids.txt ; '
            )
            if inspire_settings['convert']:
                bash_file.write(
                    f'inspire --pipeline convert --config_file {project_home}/config.yml\n'
                )

            if inspire_settings['fragger']:
                bash_file.write(
                    f'inspire --pipeline fragger --config_file {project_home}/config.yml\n'
                )

            bash_file.write(
                f'inspire --pipeline core --config_file {project_home}/config.yml\n'
            )
            bash_file.write(
                f'inspire --pipeline generateReport --config_file {project_home}/config.yml\n'
            )
            if inspire_settings['select']:
                bash_file.write(
                    f'inspire --pipeline extractCandidates --config_file {project_home}/config.yml\n'
                )
            for intermediate_file in INTERMEDIATE_FILES:
                bash_file.write(
                    f'rm -rf projects/{user}/{project_title}/inspireOutput/{intermediate_file}\n'
                )

        os.system(
            f'bash {project_home}/inspire_script.sh > {project_home}/inspire_log.txt 2>&1 &',
        )

        response = jsonify(
            message=f'http://{server_address}:5000/interact/{user}/{project_title}/inspire'
        )
    except Exception as err:
        print(err)
        response = jsonify(message=f'inSPIRE-Interact failed with error code: {err}')
        print(response)
    return response

@app.route('/interact/<user>/<project>/<workflow>', methods=['GET'])
@cross_origin()
def check_results(user, project, workflow):
    """ Check results.
    """
    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'
    status = check_pids(project_home, workflow)
    if (
        os.path.exists(f'{project_home}/proteome/pathogenProteome.fasta') or
        os.path.exists(f'{project_home}/proteomeSelect_file_list.txt')
    ):
        display_inspire_select = 'block'
    else:
        display_inspire_select = 'none'

    if status == 'waiting':
        return render_template('waiting.html', server_address=app.config[SERVER_ADDRESS_KEY])
    else:
        if display_inspire_select == 'block':
            key_file = 'potentialEpitopeCandidates.xlsx'
        else:
            key_file = 'inspire-report.html'
        
        if os.path.exists(f'{project_home}/inspireOutput/{key_file}'):
            return render_template(
                'ready.html',
                server_address=app.config[SERVER_ADDRESS_KEY],
                user=user,
                project=project,
                workflow=workflow,
                display_inspire_select=display_inspire_select,
            )
        else:
            return render_template(
                'failed.html',
                server_address=app.config[SERVER_ADDRESS_KEY],
                user=user,
                project=project,
                workflow=workflow,
            )

@app.route('/interact/get_results/<user>/<project>/<workflow>', methods=['GET'])
@cross_origin()
def get_results_file(user, project, workflow):
    """ Function to return the results files from any interact workflow.
    """
    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'
    if workflow == 'inspire':
        key_file = 'finalAssignments.csv'
        with open(
            f'{project_home}/inspireOutput/{key_file}',
            mode='r',
            encoding='UTF-8'
        ) as out_file:
            csv_data = out_file.read()
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-disposition': f'attachment; filename={user}_{project}_{key_file}'
            }
        )
    if workflow == 'inspireSelect':
        key_file = 'potentialEpitopeCandidates.xlsx'
        with open(
            f'{project_home}/inspireOutput/{key_file}',
            mode='r',
            encoding='UTF-8'
        ) as out_file:
            csv_data = out_file.read()
        return Response(
            csv_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheetv',
            headers={
                'Content-disposition': f'attachment; filename={user}_{project}_{key_file}'
            }
        )
    if workflow == 'inspireLog':
        key_file = 'inspire_log.txt'
        with open(
            f'{project_home}/{key_file}',
            mode='r',
            encoding='UTF-8'
        ) as out_file:
            csv_data = out_file.read()
        return Response(
            csv_data,
            mimetype='text/txt',
            headers={
                'Content-disposition': f'attachment; filename={user}_{project}_{key_file}'
            }
        )
    if workflow == 'performance':
        with open(
            f'{project_home}/inspireOutput/inspire-report.html',
            mode='r',
            encoding='UTF-8',
        ) as perf_file:
            contents = perf_file.read()
        return contents
    return Response()

def get_arguments():
    """ Function to collect command line arguments.

    Returns
    -------
    args : argparse.Namespace
        The parsed command line arguments.
    """
    parser = ArgumentParser(description='inSPIRE-Interactive Helper.')

    parser.add_argument(
        '--config_file',
        required=True,
        help='All configurations.',
    )
    parser.add_argument(
        '--mode',
    )

    return parser.parse_args()


def main():
    """ Main function to run inSPIRE-interactive.
    """
    args = get_arguments()

    with open(args.config_file, 'r', encoding='UTF-8') as stream:
        config_dict = yaml.safe_load(stream)
    for config_key in config_dict:
        if config_key not in ALL_CONFIG_KEYS:
            raise ValueError(f'Unrecognised key {config_key} found in config file.')

    app.config[INTERACT_HOME_KEY] = os.getcwd()
    if not os.path.exists('projects'):
        os.mkdir('projects')
    host_name = socket.gethostname()
    app.config[SERVER_ADDRESS_KEY] = socket.gethostbyname(host_name + ".local")
    app.config[FILESERVER_NAME_KEY] = config_dict.get(FILESERVER_NAME_KEY)
    app.config[FRAGGER_PATH_KEY] = config_dict.get(FRAGGER_PATH_KEY)
    app.config[FRAGGER_MEMORY_KEY] = config_dict.get(FRAGGER_MEMORY_KEY)
    app.config[MODE_KEY] = args.mode

    app.run(host='0.0.0.0', debug = False)

if __name__ == '__main__':
    main()
