""" Main api routes for inSPIRE-interactive
"""
from argparse import ArgumentParser
import os
import socket

import flask
from flask import request, Response, render_template, send_from_directory
from flask.json import jsonify
from flask_cors import cross_origin
import yaml

from inspire_interact.constants import (
    ALL_CONFIG_KEYS,
    CPUS_KEY,
    FILESERVER_NAME_KEY,
    FRAGGER_MEMORY_KEY,
    FRAGGER_PATH_KEY,
    MHCPAN_KEY,
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
    if os.path.isdir(f'{app.config[INTERACT_HOME_KEY]}/projects/{user}'):
        projects = os.listdir(f'projects/{user}')
        projects = [project for project in projects if not project.endswith('.tar')]
    else:
        os.mkdir(f'projects/{user}')
        projects = []
    response =  jsonify(message=projects)
    return response


@app.route('/interact-page/<page>', methods=['GET'])
@cross_origin()
def fetch_page_no_arguments(page):
    """ Endpoint serving the spi_serverive Home Page.
    """
    return render_template(
        f'{page}.html',
        server_address=app.config[SERVER_ADDRESS_KEY],
        mode=app.config[MODE_KEY],
    )

@app.route('/interact-page/<page>/<user>/<project>', methods=['GET'])
@cross_origin()
def fetch_page(page, user, project):
    """ Endpoint serving the spi_serverive Home Page.
    """
    if not os.path.exists(f'projects/{user}/{project}/core_metadata.yml'):
        return render_template(
            f'{page}.html',
            server_address=app.config[SERVER_ADDRESS_KEY],
            mode=app.config[MODE_KEY],
            user=user,
            project=project,
        )
    with open(f'projects/{user}/{project}/core_metadata.yml', 'r', encoding='UTF-8') as stream:
        core_config = yaml.safe_load(stream)
        variant = core_config['variant']
    if page == 'proteome':
        page += f'-{variant}'
    return render_template(
        f'{page}.html',
        server_address=app.config[SERVER_ADDRESS_KEY],
        mode=app.config[MODE_KEY],
        user=user,
        project=project,
        variant=variant,
    )

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
            f'{upload_home}/proteome_{uploaded_files[0].filename}'
        )
    elif file_type == 'proteome-select':
        uploaded_files[0].save(
            f'{upload_home}/host_{uploaded_files[0].filename}'
        )
        uploaded_files[1].save(
            f'{upload_home}/pathogen_{uploaded_files[1].filename}'
        )
        with open(f'{upload_home}/proteome_combined.fasta', mode='w', encoding='UTF-8') as total_file:
            for prot_file in (
                f'{upload_home}/host_{uploaded_files[0].filename}',
                f'{upload_home}/pathogen_{uploaded_files[1].filename}',
            ):
                with open(
                    prot_file, mode='r', encoding='UTF-8'
                ) as source_file:
                    for line in source_file:
                        total_file.write(line)
    elif file_type == 'search':
        # For search if there are multiple msms.txt, etc, we avoid overwriting
        for idx, u_file in enumerate(uploaded_files):
            renamed_file = f'{str(idx+1)}_' + u_file.filename.replace(" ", "_")
            u_file.save(
                f'{upload_home}/{renamed_file}'
            )
    else:
        # For raw files we preserve name
        for u_file in uploaded_files:
            u_file.save(
                f'{upload_home}/{u_file.filename}'
            )

    return jsonify(message='Ok')


@app.route('/interact/clearPattern/<file_type>', methods=['POST'])
@cross_origin()
def clear_file_pattern(file_type):
    """ Function for checking which files match a particular file pattern provided.
    """
    config_data = request.json
    user = config_data['user']
    project = config_data['project']
    os.system(f'rm -rf projects/{user}/{project}/{file_type}/*')
    return jsonify(message=os.listdir(f'projects/{user}/{project}/{file_type}'))

@app.route('/interact/metadata', methods=['POST'])
@cross_origin()
def upload_metadata():
    """ Function for checking which files match a particular file pattern provided.
    """
    config_data = request.json
    user = config_data.pop('user')
    project = config_data.pop('project')
    metadata_type = config_data.pop('metadata_type')
    with open(f'projects/{user}/{project}/{metadata_type}_metadata.yml', 'w', encoding='UTF-8') as yaml_out:
        yaml.dump(config_data, yaml_out)
    return jsonify(message='Ok')

@app.route('/interact/metadata/<user>/<project>/<metadata_type>', methods=['GET'])
@cross_origin()
def get_metadata(user, project, metadata_type):
    """ Function for checking which files match a particular file pattern provided.
    """
    if not os.path.exists(
        f'projects/{user}/{project}/{metadata_type}_metadata.yml'
    ):
        return jsonify(message={})
    with open(
        f'projects/{user}/{project}/{metadata_type}_metadata.yml',
        'r',
        encoding='UTF-8',
    ) as stream:
        meta_dict = yaml.safe_load(stream)
    return jsonify(message=meta_dict)

@app.route('/interact/checkPattern/<file_type>', methods=['POST'])
@cross_origin()
def check_file_pattern(file_type):
    """ Function for checking which files match a particular file pattern provided.
    """
    config_data = request.json
    user = config_data['user']
    project = config_data['project']

    if os.path.exists(
        f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}/{file_type}_file_list.txt'
    ):
        os.remove(f'projects/{user}/{project}/{file_type}_file_list.txt')

    if not os.path.exists(f'projects/{user}/{project}/{file_type}'):
        os.mkdir(f'projects/{user}/{project}/{file_type}')
        return jsonify(message=[])

    fetch_matched_files = (
        f"ls -l projects/{user}/{project}/{file_type} >> projects/{user}/{project}/{file_type}_file_list.txt"
    )

    os.system(fetch_matched_files)

    with open(
        f'projects/{user}/{project}/{file_type}_file_list.txt', mode='r', encoding='UTF-8'
    ) as list_file:
        file_list = list_file.readlines()
        all_files = [x.split()[-1].split('\n')[0] for x in file_list][1:]

    return jsonify(message=all_files)


@app.route('/interact-home', methods=['GET'])
@cross_origin()
def interact_home():
    """ Endpoint serving the inspire_interactive Home Page.
    """
    return render_template(
        'home.html',
        server_address=app.config[SERVER_ADDRESS_KEY],
        mode=app.config[MODE_KEY],
    )


@app.route('/interact', methods=['GET'])
@cross_origin()
def interact_landing_page():
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
        project_home = f'{home_key}/projects/{user}/{project_title}'

        inspire_settings = prepare_inspire(config_dict, project_home, app.config)

        with open(
            f'projects/{user}/{project_title}/inspire_script.sh',
            'w',
            encoding='UTF-8'
        ) as bash_file:
            bash_file.write(
                f'echo $$ > {project_home}/inspire_pids.txt ;\n'
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
            if inspire_settings['quantify']:
                bash_file.write(
                    f'inspire --pipeline quantify --config_file {project_home}/config.yml\n'
                )
                bash_file.write(
                    f'inspire --pipeline analysis --config_file {project_home}/config.yml\n'
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
    
    if False:
        host_name = socket.gethostname()
        app.config[SERVER_ADDRESS_KEY] = socket.gethostbyname(host_name + ".local")
    else:
        app.config[SERVER_ADDRESS_KEY] = '127.0.0.1'

    app.config[FILESERVER_NAME_KEY] = config_dict.get(FILESERVER_NAME_KEY)
    app.config[MHCPAN_KEY] = config_dict.get(MHCPAN_KEY)
    app.config[FRAGGER_PATH_KEY] = config_dict.get(FRAGGER_PATH_KEY)
    app.config[FRAGGER_MEMORY_KEY] = config_dict.get(FRAGGER_MEMORY_KEY)
    app.config[CPUS_KEY] = config_dict.get(CPUS_KEY, 1)
    app.config[MODE_KEY] = args.mode

    app.run(host='0.0.0.0', debug = False)

if __name__ == '__main__':
    main()
