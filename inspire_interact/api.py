""" Main api routes for inSPIRE-interactive
"""
from argparse import ArgumentParser
import os
import shutil
import socket
import time

import flask
from flask import request, Response, render_template, send_file, send_from_directory
from flask.json import jsonify
from flask_cors import cross_origin
from jinja2.exceptions import TemplateNotFound
import pandas as pd
import yaml

from inspire_interact.clean_up import (
    clear_queue,
    cancel_job_helper,
)
from inspire_interact.constants import (
    ALL_CONFIG_KEYS,
    CPUS_KEY,
    FRAGGER_MEMORY_KEY,
    FRAGGER_PATH_KEY,
    KEY_FILES,
    MHCPAN_KEY,
    INTERACT_HOME_KEY,
    MODE_KEY,
    QUEUE_PATH,
    RESCORE_COMMAND_KEY,
    SERVER_ADDRESS_KEY,
    SKYLINE_RUNNER_KEY,
    ZIP_PATHS,
)
from inspire_interact.handle_results import (
    create_queue_fig,
    deal_with_failure,
    deal_with_queue,
    deal_with_success,
    deal_with_waiting,
    fetch_queue_and_task,
    safe_fetch,
)
from inspire_interact.inspire_execute import execute_inspire
from inspire_interact.utils import (
    check_pids,
    generate_raw_file_table,
    format_header_and_footer,
    read_meta,
)

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
        projects = sorted(os.listdir(f'projects/{user}'))
        projects = [project for project in projects if not project.endswith('.zip')]
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
    additional_args = format_header_and_footer(app.config[SERVER_ADDRESS_KEY])
    try:
        if page == 'view-queue':
            create_queue_fig(
                app.config[INTERACT_HOME_KEY],
                f'{app.config[INTERACT_HOME_KEY]}/locks/'
            )
            additional_args['queue_svg'] = safe_fetch(
                f'{app.config[INTERACT_HOME_KEY]}/locks/queue.svg'
            )
        return render_template(
            f'{page}.html',
            server_address=app.config[SERVER_ADDRESS_KEY],
            mode=app.config[MODE_KEY],
            **additional_args
        )
    except TemplateNotFound:
        return render_template(
            '404.html',
            **additional_args,
        ), 404


@app.route('/interact-page/<page>/<user>/<project>', methods=['GET'])
@cross_origin()
def fetch_page(page, user, project):
    """ Endpoint serving the spi_serverive Home Page.
    """
    header_and_footer = format_header_and_footer(app.config[SERVER_ADDRESS_KEY])
    project_home = f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}'
    if not os.path.exists(f'{project_home}/core_metadata.yml'):
        try:
            return render_template(
                f'{page}.html',
                server_address=app.config[SERVER_ADDRESS_KEY],
                mode=app.config[MODE_KEY],
                user=user,
                project=project,
                **header_and_footer,
            )
        except TemplateNotFound:
            return render_template('404.html', **header_and_footer), 404

    try:
        core_config = read_meta(project_home, 'core')
        variant = core_config['variant']
    except:
        time.sleep(3)
        core_config = read_meta(project_home, 'core')
        variant = core_config['variant']

    if page == 'proteome':
        page += f'-{variant}'
    try:
        if page == 'parameters':
            html_table = generate_raw_file_table(user, project, app, variant)
            return render_template(
                f'{page}.html',
                server_address=app.config[SERVER_ADDRESS_KEY],
                mode=app.config[MODE_KEY],
                user=user,
                project=project,
                variant=variant,
                html_table=html_table,
                **header_and_footer,
            )

        return render_template(
            f'{page}.html',
            server_address=app.config[SERVER_ADDRESS_KEY],
            mode=app.config[MODE_KEY],
            user=user,
            project=project,
            variant=variant,
            **header_and_footer,
        )
    except TemplateNotFound:
        return render_template('404.html', **header_and_footer), 404


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
        with open(
            f'{upload_home}/proteome_combined.fasta', mode='w', encoding='UTF-8',
        ) as total_file:
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

@app.route('/interact/metadata', methods=['POST'])
@cross_origin()
def upload_metadata():
    """ Function for checking which files match a particular file pattern provided.
    """
    config_data = request.json
    user = config_data.pop('user')
    project = config_data.pop('project')
    metadata_type = config_data.pop('metadata_type')
    with open(
        f'projects/{user}/{project}/{metadata_type}_metadata.yml',
        'w',
        encoding='UTF-8'
    ) as yaml_out:
        yaml.dump(config_data, yaml_out)
    return jsonify(message='Ok')


@app.route('/interact/metadata/<user>/<project>/<metadata_type>', methods=['GET'])
@cross_origin()
def get_metadata(user, project, metadata_type):
    """ Function for checking which files match a particular file pattern provided.
    """
    project_home = f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}'
    meta_dict = read_meta(project_home, metadata_type)
    return jsonify(message=meta_dict)


@app.route('/interact/checkPattern/<file_type>', methods=['POST'])
@cross_origin()
def check_file_pattern(file_type):
    """ Function for checking which files match a particular file pattern provided.
    """
    config_data = request.json
    user = config_data['user']
    project = config_data['project']
    project_home = f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}'

    if not os.path.exists(f'{project_home}/{file_type}'):
        os.mkdir(f'{project_home}/{file_type}')
        return jsonify(message=[])

    all_files = os.listdir(f'{project_home}/{file_type}')

    return jsonify(message=all_files)


@app.route('/interact/clearPattern/<file_type>', methods=['POST'])
@cross_origin()
def clear_file_pattern(file_type):
    """ Function for checking which files match a particular file pattern provided.
    """
    config_data = request.json
    user = config_data['user']
    project = config_data['project']
    shutil.rmtree(
        f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}/{file_type}'
    )
    os.mkdir(
        f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}/{file_type}'
    )
    return jsonify(message=os.listdir(f'projects/{user}/{project}/{file_type}'))


@app.route('/interact', methods=['GET'])
@cross_origin()
def interact_landing_page():
    """ Endpoint serving the starting page.
    """
    header_and_footer = format_header_and_footer(app.config[SERVER_ADDRESS_KEY])
    usernames = sorted(os.listdir(f'{app.config[INTERACT_HOME_KEY]}/projects'))
    option_list = [
        f'<option value="{username}">{username}</option>' for username in usernames
    ]
    options_html = ' '.join(option_list)
    return render_template(
        'index.html',
        server_address=app.config[SERVER_ADDRESS_KEY],
        user_list=options_html,
        mode=app.config[MODE_KEY],
        **header_and_footer,
    )


@app.route('/interact/delete', methods=['POST'])
@cross_origin()
def delete_project():
    """ Function allow deletion of all project data.
    """
    config_dict = request.json
    user = config_dict['user']
    project = config_dict['project']
    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'
    if os.path.exists(project_home):
        shutil.rmtree(project_home)
    return jsonify(
        message=(
            'Project deleted.'
        )
    )


@app.route('/interact/download/<user>/<project>', methods=['GET'])
@cross_origin()
def download_project(user, project):
    """ Function allow download of all project data.
    """
    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'
    if os.path.exists(f'{project_home}/config.yml'):
        shutil.copyfile(f'{project_home}/config.yml', f'{project_home}/inspireOutput/config.yml')
    if not os.path.exists(f'{project_home}/inspireOutput'):
        os.mkdir((f'{project_home}/inspireOutput'))
    shutil.make_archive(f'{project_home}/inspireOutput', 'zip', f'{project_home}/inspireOutput')
    return send_file(f'{project_home}/inspireOutput.zip', mimetype='zip', as_attachment=True)


@app.route('/interact/cancel', methods=['POST'])
@cross_origin()
def cancel_job():
    """ Function to cancel an inSPIRE execution.
    """
    config_dict = request.json

    user = config_dict.get('user')
    project = config_dict.get('project')
    job_id = config_dict.get('jobID')
    if job_id is not None:
        job_id = int(job_id)

    cancel_message = cancel_job_helper(app.config[INTERACT_HOME_KEY], user, project, job_id)

    return jsonify(message=cancel_message)


@app.route('/interact/inspire', methods=['POST'])
@cross_origin()
def run_inspire_core():
    """ Run the inSPIRE core pipeline.
    """
    config_dict = request.json
    user = config_dict['user']
    project = config_dict['project']

    project_home = f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}'
    response = jsonify(
        message=f'http://{app.config[SERVER_ADDRESS_KEY]}:5000/interact/{user}/{project}/inspire'
    )

    try:
        # If task is already running or queued, do nothing:
        if check_pids(project_home, 'inspire') == 'waiting':
            return response

        execute_inspire(app.config, project_home, config_dict)

    except Exception as err:
        return jsonify(message=f'inSPIRE-Interact failed with error code: {err}')

    return response

@app.route('/interact/<user>/<project>/<workflow>', methods=['GET'])
@cross_origin()
def check_results(user, project, workflow):
    """ Check results.
    """
    project_home = f'{app.config[INTERACT_HOME_KEY]}/projects/{user}/{project}'
    server_address = app.config[SERVER_ADDRESS_KEY]
    header_and_footer = format_header_and_footer(app.config[SERVER_ADDRESS_KEY])

    if not os.path.exists(project_home):
        return render_template('404.html', **header_and_footer), 404

    time.sleep(0.5)
    status = check_pids(project_home, workflow)

    # Task incomplete - either running or queueing (or total failure)
    if status == 'waiting':
        queue_df, task_id = fetch_queue_and_task(project_home, app.config[INTERACT_HOME_KEY])

        if not queue_df.shape[0]:
            time.sleep(2)
            queue_df, task_id = fetch_queue_and_task(
                project_home, app.config[INTERACT_HOME_KEY],
            )

        if not queue_df.shape[0]:
            return deal_with_failure(
                project_home,
                server_address,
                user,
                project,
                workflow,
                header_and_footer
            )

        if int(queue_df['taskID'].iloc[0]) == task_id:
            return deal_with_waiting(
                project_home,
                server_address,
                user,
                project,
                header_and_footer,
            )

        return deal_with_queue(
            app.config[INTERACT_HOME_KEY],
            project_home,
            server_address,
            header_and_footer,
        )

    # Task complete : either in success or failure.
    with open(f'projects/{user}/{project}/core_metadata.yml', 'r', encoding='UTF-8') as stream:
        core_config = yaml.safe_load(stream)
        variant = core_config['variant']
    if variant == 'pathogen':
        inspire_select_visible = 'visible'
        key_file = 'epitope/potentialEpitopeCandidates.xlsx'
    else:
        inspire_select_visible = 'hidden'
        key_file = 'inspire-report.html'

    if os.path.exists(f'{project_home}/inspireOutput/{key_file}'):
        return deal_with_success(
            project_home,
            server_address,
            user,
            project,
            workflow,
            inspire_select_visible,
            header_and_footer,
        )
    return deal_with_failure(
        project_home,
        server_address,
        user,
        project,
        workflow,
        header_and_footer,
    )


@app.route('/interact/get_results/<user>/<project>/<workflow>', methods=['GET'])
@cross_origin()
def get_results_file(user, project, workflow):
    """ Function to return the results files from any interact workflow.
    """
    home_key= app.config[INTERACT_HOME_KEY]
    server_address = app.config[SERVER_ADDRESS_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'

    # The quantification results require a zip archive
    if workflow in ('quantification', 'inspirePathogen'):
        if os.path.exists(f'{project_home}/{ZIP_PATHS[workflow]}.zip'):
            os.remove(f'{project_home}/{ZIP_PATHS[workflow]}.zip')

        shutil.make_archive(
            f'{project_home}/{ZIP_PATHS[workflow]}',
            'zip',
            f'{project_home}/{ZIP_PATHS[workflow]}',
        )

    # The following results require the relevant results file to be sent:
    if workflow in (
        'epitopePlots',
        'psms',
        'peptides',
        'inspireLog',
        'inspirePathogen',
        'quantification'
    ):
        if os.path.exists(f'{project_home}/{KEY_FILES[workflow]}'):
            kwargs = {}
            if KEY_FILES[workflow].endswith('.zip'):
                kwargs['mimetype'] = 'zip'
                kwargs['as_attachment'] = True
            return send_file(f'{project_home}/{KEY_FILES[workflow]}', **kwargs)

    # The following send html reports
    if workflow in ('epitopeReport', 'performance', 'quantReport'):
        if (contents := safe_fetch(f'{project_home}/{KEY_FILES[workflow]}')):
            if workflow == 'epitopeReport':
                contents = contents.replace(
                    f'{project_home}/inspireOutput/epitope/spectralPlots.pdf',
                    f'http://{server_address}:5000/interact/get_results/{user}/{project}/epitopePlots',
                )

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
        default='server',
        required=False,
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
    app.config[INTERACT_HOME_KEY] = app.config[INTERACT_HOME_KEY].replace(
        '\\', '/'
    )
    if not os.path.exists('projects'):
        os.mkdir('projects')
    if not os.path.exists('locks'):
        os.mkdir('locks')
    if not os.path.exists(QUEUE_PATH.format(
        home_key=app.config[INTERACT_HOME_KEY])
    ):
        empty_queue_df = pd.DataFrame({
            'user': [],
            'project': [],
            'taskID': [],
            'status': [],
        })
        empty_queue_df.to_csv(QUEUE_PATH.format(
            home_key=app.config[INTERACT_HOME_KEY]), index=False
        )

    if args.mode == 'local':
        host_name = socket.gethostname()
        app.config[SERVER_ADDRESS_KEY] = host_name
    elif args.mode == 'server':
        host_name = socket.gethostname()
        app.config[SERVER_ADDRESS_KEY] = socket.gethostbyname(host_name + ".local")
    else:
        raise ValueError(f'Unknown mode {args.mode} requested')

    app.config[MHCPAN_KEY] = config_dict.get(MHCPAN_KEY)
    app.config[FRAGGER_PATH_KEY] = config_dict.get(FRAGGER_PATH_KEY)
    app.config[FRAGGER_MEMORY_KEY] = config_dict.get(FRAGGER_MEMORY_KEY)
    app.config[CPUS_KEY] = config_dict.get(CPUS_KEY, 1)
    app.config[SKYLINE_RUNNER_KEY] = config_dict.get(SKYLINE_RUNNER_KEY)
    app.config[RESCORE_COMMAND_KEY] = config_dict.get(RESCORE_COMMAND_KEY)
    if app.config[SKYLINE_RUNNER_KEY] is not None:
         app.config[SKYLINE_RUNNER_KEY] = app.config[SKYLINE_RUNNER_KEY].replace(
            '\\', '/'
        )

    app.config[MODE_KEY] = args.mode

    app.run(host='0.0.0.0', debug = False)

    print('Quitting, first clearing queue.')
    clear_queue(app.config[INTERACT_HOME_KEY])


if __name__ == '__main__':
    main()
