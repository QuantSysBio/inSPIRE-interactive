""" Main api routes for inSPIRE-interactive
"""
from argparse import ArgumentParser
import os
import shutil
import signal
import socket
import time

import flask
from flask import request, Response, render_template, send_file, send_from_directory
from flask.json import jsonify
from flask_cors import cross_origin
from markupsafe import Markup
import pandas as pd
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
from inspire_interact.utils import (
    check_pids,
    create_status_fig,
    check_queue,
    create_queue_fig,
    get_inspire_increase,
    get_pids,
    get_quant_count,
    get_tasks, prepare_inspire,
    write_inspire_task
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
    try:
        with open(f'projects/{user}/{project}/core_metadata.yml', 'r', encoding='UTF-8') as stream:
            core_config = yaml.safe_load(stream)
            variant = core_config['variant']
    except:
        time.sleep(3)
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

@app.route('/interact/delete', methods=['POST'])
@cross_origin()
def delete_project():
    config_dict = request.json
    user = config_dict['user']
    project = config_dict['project']

    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'
    if os.path.exists(project_home):
        shutil.rmtree(project_home)
        message=(
            'Project deleted.'
        )
    return jsonify(
        message=(
            'Project deleted.'
        )
    )


@app.route('/interact/download/<user>/<project>', methods=['GET'])
@cross_origin()
def download_project(user, project):
    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'

    shutil.copyfile(f'{project_home}/config.yml', f'{project_home}/inspireOutput/config.yml')
    shutil.make_archive(f'{project_home}/inspireOutput', 'zip', f'{project_home}/inspireOutput')
    return send_file(f'{project_home}/inspireOutput.zip')



@app.route('/interact/cancel', methods=['POST'])
@cross_origin()
def cancel_job():
    config_dict = request.json
    user = config_dict['user']
    project = config_dict['project']

    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'

    pids = get_pids(project_home, 'inspire')
    if pids is None:
        return jsonify(
            message=(
                'No task was running. Please refresh the page.'
            )
        )

    task_killed = False
    for pid in pids:
        try:
            os.kill(int(pid), signal.SIGTERM) #or signal.SIGKILL 
            task_killed = True
        except OSError:
            continue

    if not task_killed:
        return jsonify(
            message=(
                'No task was running. Please refresh the page.'
            )
        )

    os.system(
        f'python inspire_interact/remove_from_queue.py  {user} {project}\n'
    )
    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    task_df['status'] = 'Job Cancelled'
    task_df.to_csv(f'{project_home}/taskStatus.csv', index=False)

    return jsonify(
        message=(
            'Task cancelled. Please refresh the page.'
        )
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
        print(project_home)

        if check_pids(project_home, 'inspire') == 'waiting':
            return jsonify(
                message=(
                    'Task is already running. Check status at ' +
                    f'http://{server_address}:5000/interact/{user}/{project_title}/inspire'
                )
            )
        
        if check_queue(user, project_title):
            return jsonify(
                message=(
                    'Task is already queued. Check status at ' +
                    f'http://{server_address}:5000/interact/{user}/{project_title}/inspire'
                )
            )

        inspire_settings = prepare_inspire(config_dict, project_home, app.config)
        print(inspire_settings)
        get_tasks(inspire_settings, project_home)

        with open(
            f'projects/{user}/{project_title}/inspire_script.sh',
            'w',
            encoding='UTF-8'
        ) as bash_file:
            bash_file.write(
                f'echo $$ > {project_home}/inspire_pids.txt ;\n'
            )
            bash_file.write(
                f'python inspire_interact/add_to_queue.py {user} {project_title}\n'
            )
            bash_file.write(
                f'python inspire_interact/check_queue.py {user} {project_title}\n'
            )
            bash_file.write(
                f'python inspire_interact/check_status.py start 0 {project_home}\n'
            )
            if inspire_settings['convert']:
                write_inspire_task(bash_file, project_home, 'convert')

            if inspire_settings['fragger']:
                write_inspire_task(bash_file, project_home, 'fragger')

            write_inspire_task(bash_file, project_home, 'prepare')
            write_inspire_task(bash_file, project_home, 'predictSpectra')
            if inspire_settings['binding']:
                write_inspire_task(bash_file, project_home, 'predictBinding')
            write_inspire_task(bash_file, project_home, 'featureGeneration')
            write_inspire_task(bash_file, project_home, 'featureSelection+')
            write_inspire_task(bash_file, project_home, 'generateReport')

            if inspire_settings['quantify']:
                write_inspire_task(bash_file, project_home, 'quantify')
                if inspire_settings['pathogen']:
                    write_inspire_task(bash_file, project_home, 'quantReport')

            if inspire_settings['pathogen']:
                write_inspire_task(bash_file, project_home, 'extractCandidates')

            for intermediate_file in INTERMEDIATE_FILES:
                bash_file.write(
                    f'rm -rf projects/{user}/{project_title}/inspireOutput/{intermediate_file}\n'
                )

            bash_file.write(
                f'python inspire_interact/remove_from_queue.py  {user} {project_title}\n'
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
        os.path.exists(f'{project_home}/proteome-select') or
        os.path.exists(f'{project_home}/proteomeSelect_file_list.txt')
    ):
        inspire_select_visible = 'visible'
    else:
        inspire_select_visible = 'hidden'

    if status == 'waiting':
        create_queue_fig(project_home)
        create_status_fig(project_home)

        with open(f'{project_home}/inspire_pids.txt', 'r') as pid_file:
            task_id = int(pid_file.readline().strip())

        queue_df = pd.read_csv('locks/inspireQueue.csv')
        if int(queue_df['taskID'].iloc[0]) == task_id:
            with open(f'{project_home}/progress.html', 'r') as html_file:
                progress_html = html_file.read()
            return render_template(
                'waiting.html',
                progress_html=progress_html,
                project=project,
                server_address=app.config[SERVER_ADDRESS_KEY],
                user=user,
            )
        else:
            with open(f'{project_home}/queue.svg', 'r') as svg_file:
                queue_svg = Markup(svg_file.read())

            return render_template(
                'queued.html',
                server_address=app.config[SERVER_ADDRESS_KEY],
                queue_svg=queue_svg,
            )

    else:
        if inspire_select_visible == 'visible':
            key_file = 'epitope/potentialEpitopeCandidates.xlsx'
        else:
            key_file = 'inspire-report.html'
        
        if os.path.exists(f'{project_home}/inspireOutput/{key_file}'):
            create_status_fig(project_home)
            with open(f'{project_home}/progress.svg', 'r') as html_file:
                progress_html = html_file.read()

            if os.path.exists(f'{project_home}/inspireOutput/img/psm_fdr_curve.svg'):
                with open(f'{project_home}/inspireOutput/img/psm_fdr_curve.svg', 'r') as html_file:
                    psm_fdr_html = html_file.read()
            else:
                psm_fdr_html = ''

            if os.path.exists(f'{project_home}/inspireOutput/img/epitope_bar_plot.svg'):
                with open(f'{project_home}/inspireOutput/img/epitope_bar_plot.svg', 'r') as svg_file:
                    ep_bar = svg_file.read()
            else:
                ep_bar = ''

            if os.path.exists(f'{project_home}/inspireOutput/img/peptide_volcano.svg'):
                with open(f'{project_home}/inspireOutput/img/peptide_volcano.svg', 'r') as html_file:
                    quant_html = html_file.read()
            elif os.path.exists(f'{project_home}/inspireOutput/img/norm_correlation.svg'):
                with open(f'{project_home}/inspireOutput/img/norm_correlation.svg', 'r') as html_file:
                    quant_html = html_file.read()
            else:
                quant_html = ''

            return render_template(
                'ready.html',
                server_address=app.config[SERVER_ADDRESS_KEY],
                user=user,
                project=project,
                workflow=workflow,
                inspire_select_visible=inspire_select_visible,
                psm_fdr_html=psm_fdr_html,
                ep_bar=ep_bar,
                quant_html=quant_html,
                progress_html=progress_html,
                inspire_increase=get_inspire_increase(project_home, 'total'),
                pathogen_increase=get_inspire_increase(project_home, 'pathogen'),
                inspire_quantified_count=get_quant_count(project_home)
            )
        else:
            create_status_fig(project_home)
            with open(f'{project_home}/progress.html', 'r') as html_file:
                progress_html = html_file.read()
            return render_template(
                'failed.html',
                server_address=app.config[SERVER_ADDRESS_KEY],
                user=user,
                project=project,
                workflow=workflow,
                progress_html=progress_html,
            )

@app.route('/interact/get_results/<user>/<project>/<workflow>', methods=['GET'])
@cross_origin()
def get_results_file(user, project, workflow):
    """ Function to return the results files from any interact workflow.
    """
    home_key= app.config[INTERACT_HOME_KEY]
    server_address = app.config[SERVER_ADDRESS_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'
    if workflow == 'inspire':
        return send_file(f'{project_home}/inspireOutput/finalPsmAssignments.csv')

    if workflow == 'inspireSelect':
        return send_file(f'{project_home}/inspireOutput/epitope/potentialEpitopeCandidates.xlsx')

    if workflow == 'inspireLog':
        return send_file(f'{project_home}/inspire_log.txt')
    
    if workflow == 'quantification':
        shutil.make_archive(f'{project_home}/inspireOutput/quant', 'zip', f'{project_home}/inspireOutput/quant')
        return send_file(f'{project_home}/inspireOutput/quant.zip')

    if workflow == 'epitopeReport':
        with open(
            f'{project_home}/inspireOutput/epitope/inspire-epitope-report.html',
            mode='r',
            encoding='UTF-8',
        ) as perf_file:
            contents = perf_file.read()
            contents = contents.replace(
                f'{project_home}/inspireOutput/epitope/spectralPlots.pdf',
                f'http://{server_address}:5000/interact/get_results/{user}/{project}/epitopePlots'
            )
        return contents
    
    if workflow == 'epitopePlots':
        return send_file(
            f'{project_home}/inspireOutput/epitope/spectralPlots.pdf'
        )

    if workflow == 'performance':
        with open(
            f'{project_home}/inspireOutput/inspire-report.html',
            mode='r',
            encoding='UTF-8',
        ) as perf_file:
            contents = perf_file.read()
        return contents
    
    if workflow == 'quantReport':
        with open(
            f'{project_home}/inspireOutput/quant/inspire-quant-report.html',
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
    # waitress.serve(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
