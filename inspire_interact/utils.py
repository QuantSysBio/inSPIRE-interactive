""" Utility functions for inSPIRE-interact.
"""
import ast
from copy import deepcopy
import os

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import yaml

from inspire_interact.constants import (
    CPUS_KEY,
    FRAGGER_MEMORY_KEY,
    FRAGGER_PATH_KEY,
    INTERACT_HOME_KEY,
    MHCPAN_KEY,
    SERVER_ADDRESS_KEY,
)

def generate_raw_file_table(user, project, app, variant):
    home_key= app.config[INTERACT_HOME_KEY]
    project_home = f'{home_key}/projects/{user}/{project}'
    
    if variant == 'pathogen':
        html_table = '''
            <tr align="center" valign="center">
                <td><b>Raw File</b></td>
                <td><b>Biological Sample</b></td>
                <td><b>Infected Sample</b></td>
            </tr>
        '''
    else:
        html_table = '''
            <tr align="center" valign="center">
                <td><b>Raw File</b></td>
                <td><b>Biological Sample</b></td>
            </tr>
        '''

    sample_files = sorted(list(set([
        file_name[:-4] for file_name in os.listdir(
            f'{project_home}/ms'
        ) if (
            file_name.lower().endswith('.raw') or 
            file_name.lower().endswith('.mgf')
        )
    ])))

    for sample_idx, sample_name in enumerate(sample_files):
        html_table += f'''
            <tr align="center" valign="center">
            <td>{sample_name}</td>
			<td>
                <input type="text" class="sample-value" value="{sample_idx+1}"
                    onkeypress="textSubmit(event, '{app.config[SERVER_ADDRESS_KEY]}', 'noAction')"/>
            </td>
        '''
        if variant == 'pathogen':
            html_table += f'''
                <td>
					<input type="checkbox" class="infection-checkbox" style="align: center" id="{sample_name}_infected" name="{sample_name}_infected">
				</td>
            '''
        html_table += '</tr>'

    return html_table


def write_inspire_task(bash_file, project_home, task, interact_home):
    bash_file.write(
        f'inspire --pipeline {task} --config_file {project_home}/config.yml\n'
    )
    bash_file.write(
        f'interact-queue --project_home {project_home} ' +
        f' --interact_home {interact_home}' +
        f' --queue_task update --inspire_task {task} --inspire_status $?\n'
    )
    bash_file.write(
        'if [ "$?" -ne "0" ]\n' +
        '  then\n' +
        f'    interact-queue --project_home {project_home} --interact_home {interact_home} ' +
        ' --queue_task remove\n'
    )
    # Some tasks do not need to block execution:
    if task not in ('predictBinding', 'quantify', 'generateReport'):
        bash_file.write(
            '    exit 0\n'
        )
    bash_file.write(
        'fi\n'
    )

def prepare_inspire(config_dict, project_home, app_config):
    """ Function to prepare the inSPIRE run.
    """
    inspire_settings = {
        'convert': False,
        'fragger': False,
        'pathogen': False,
    }

    inspire_settings['quantify'] = bool(config_dict['runQuantification'])

    output_config = {
        'experimentTitle': config_dict['project'],
        'scansFormat': 'mgf',
        'outputFolder': f'{project_home}/inspireOutput',
        'mzAccuracy': float(config_dict['mzAccuracy']),
        'ms1Accuracy': float(config_dict['ms1Accuracy']),
        'mzUnits': config_dict['mzUnits'],
        'silentExecution': True,
        'reuseInput': True,
        'fraggerPath': app_config[FRAGGER_PATH_KEY],
        'fraggerMemory': app_config[FRAGGER_MEMORY_KEY],
        'nCores': app_config[CPUS_KEY],
        'technicalReplicates': config_dict['technicalReplicates'],
    }

    if not os.path.exists(
        f'{project_home}/search_metadata.yml'
    ):
        return {}
    else:
        with open(
            f'{project_home}/search_metadata.yml',
            'r',
            encoding='UTF-8',
        ) as stream:
            meta_dict = yaml.safe_load(stream)
        output_config['searchEngine'] = meta_dict.get('searchEngine', 'msfragger')
        inspire_settings['fragger'] = bool(meta_dict.get('runFragger', 1))

    if 'useBindingAffinity' in config_dict:
        output_config['useBindingAffinity'] = config_dict['useBindingAffinity']
        output_config['alleles'] = [
            elem.strip() for elem in  config_dict["alleles"].split(",")
        ]
        output_config['netMHCpan'] = app_config[MHCPAN_KEY]
        inspire_settings['binding'] = True
    else:
        inspire_settings['binding'] = False

    if not inspire_settings['fragger']:
        output_config['searchResults'] = [
            f'{project_home}/search/{filename}' for filename in os.listdir(
                f'{project_home}/search/'
            )
        ]

    output_config['scansFolder'] = f'{project_home}/ms'

    ms_files = os.listdir(f'{project_home}/ms')

    raw_files = [ms_file for ms_file in ms_files if ms_file.lower().endswith('.raw')]
    mgf_files = [ms_file for ms_file in ms_files if ms_file.lower().endswith('.mgf')]
    if len(raw_files) != len(mgf_files):
        inspire_settings['convert'] = True

    if output_config['searchEngine'] in ('mascot', 'msfragger'):
        output_config['rescoreMethod'] = 'percolatorSeparate'
    else:
        output_config['rescoreMethod'] = 'percolator'

    
    if os.path.exists(f'{project_home}/proteome'):
        proteome_files = os.listdir(f'{project_home}/proteome')
        if len(proteome_files) > 0:
            prot_file_name = proteome_files[0]
            output_config['proteome'] = f'{project_home}/proteome/{prot_file_name}'
            output_config['inferProteins'] = True
    else:
        proteome_files = os.listdir(f'{project_home}/proteome-select')
        inspire_settings['pathogen'] = True
        output_config['proteome'] = f'{project_home}/proteome-select/proteome_combined.fasta'
        path_name = [
            prot_file for prot_file in proteome_files if prot_file.startswith('pathogen_')
        ][0]
        host_name = [
            prot_file for prot_file in proteome_files if prot_file.startswith('host_')
        ][0]
        output_config['pathogenProteome'] = f'{project_home}/proteome-select/{path_name}'
        output_config['hostProteome'] = f'{project_home}/proteome-select/{host_name}'
        output_config['controlFlags'] = [
            elem.strip() for elem in config_dict["controlFlags"].split(",") if elem
        ]
        output_config['inferProteins'] = True
    for config_key, config_value in config_dict['additionalConfigs'].items():
        try:
            output_config[config_key] = ast.literal_eval(config_value)
        except:
            output_config[config_key] = config_value


    with open(f'{project_home}/config.yml', 'w', encoding='UTF-8') as yaml_out:
        yaml.dump(output_config, yaml_out)

    return inspire_settings


def get_quant_count(project_home):
    if os.path.exists(f'{project_home}/inspireOutput/quant/quantified_per_file.csv'):
        quant_df = pd.read_csv(f'{project_home}/inspireOutput/quant/quantified_per_file.csv')
        quant_count = quant_df.shape[0]
    else:
        quant_count = 0

    return f'inSPIRE quantified {quant_count} peptides via Skyline.'


def get_inspire_increase(project_home, variant):
    if variant == 'total':
        if os.path.exists(f'{project_home}/inspireOutput/final.percolator.psms.txt'):
            inspire_df = pd.read_csv(f'{project_home}/inspireOutput/final.percolator.psms.txt', sep='\t')
        elif os.path.exists(f'{project_home}/inspireOutput/final.percolatorSeparate.psms.txt'):
            inspire_df = pd.read_csv(f'{project_home}/inspireOutput/final.percolatorSeparate.psms.txt', sep='\t')
        else:
            inspire_df = pd.DataFrame({'q-value': []})
        inspire_count = len(inspire_df[inspire_df['q-value'] < 0.01])

        if os.path.exists(f'{project_home}/inspireOutput/non_spectral.percolator.psms.txt'):
            ns_df = pd.read_csv(f'{project_home}/inspireOutput/non_spectral.percolator.psms.txt', sep='\t')
        elif os.path.exists(f'{project_home}/inspireOutput/non_spectral.percolatorSeparate.psms.txt'):
            ns_df = pd.read_csv(f'{project_home}/inspireOutput/non_spectral.percolatorSeparate.psms.txt', sep='\t')
        else:
            ns_df = pd.DataFrame({'q-value': []})
        ns_count = len(ns_df[ns_df['q-value'] < 0.01])

        if ns_count <= 0:
            return ''
        increase = round(100*(inspire_count - ns_count)/ns_count, 2)

        return f'inSPIRE increased overall PSM yield by {increase}% at 1% FDR.'
    else:
        if not os.path.exists(f'{project_home}/inspireOutput/epitope/potentialEpitopeCandidates.csv'):
            return 'No epitope candidates found.'
        pathogen_df = pd.read_csv(f'{project_home}/inspireOutput/epitope/potentialEpitopeCandidates.csv')
        shared_count = len(pathogen_df[
            pathogen_df['foundBySearchEngine'] == 'Yes'
        ])
        inspire_count = len(pathogen_df[
            pathogen_df['foundBySearchEngine'] == 'No'
        ])
        if shared_count == 0:
            increase = '>100'
        else:
            increase = round(100*inspire_count/shared_count, 2)

        return f'inSPIRE increased pathogen peptide yield by {increase}%.'

def check_queue(interact_home, user, project):
    if not os.path.exists(f'{interact_home}/locks/inspireQueue.csv'):
        return False
    queue_df = pd.read_csv(f'{interact_home}/locks/inspireQueue.csv')
    filtered_queue = queue_df[
        (queue_df['user'] == user) &
        (queue_df['project'] == project)
    ]
    if filtered_queue.shape[0]:
        return True
    return False


def get_pids(project_home, workflow):
    if not os.path.exists(f'{project_home}/{workflow}_pids.txt'):
        return None
    
    with open(f'{project_home}/{workflow}_pids.txt', 'r', encoding='UTF-8') as file:
        lines = file.readlines()
        pids = [line.rstrip() for line in lines]
    return pids


def check_pids(project_home, workflow):
    """ Function to check if process IDs are still running.
    """
    if not os.path.exists(f'{project_home}/{workflow}_pids.txt'):
        return 'clear'

    with open(f'{project_home}/{workflow}_pids.txt', 'r', encoding='UTF-8') as file:
        lines = file.readlines()
        pids = [line.rstrip() for line in lines]

    for pid in pids:
        if pid:
            try:
                os.kill(int(pid), 0)
            except OSError:
                continue
            else:
                return 'waiting'

    return 'done'

TASKS = [
    ('convert', 'Converting MS Data'),
    ('fragger', 'Executing MSFragger'),
    ('prepare', 'Preparing results'),
    ('predictSpectra', 'Predicting spectra'),
    ('predictBinding', 'Predicting binding'),
    ('featureGeneration', 'Generating features'),
    ('featureSelection+', 'Executing rescoring'),
    ('generateReport', 'Creating report'),
    ('quantify', 'Quantifying peptides'),
    ('extractCandidates', 'Finding pathogen peptides'),
]

def get_tasks(inspire_settings, project_home):
    tasks = deepcopy(TASKS)
    if not inspire_settings['convert']:
        tasks = [task for task in tasks if task[0] != 'convert']
    if not inspire_settings['fragger']:
        tasks = [task for task in tasks if task[0] != 'fragger']
    if not inspire_settings['binding']:
        tasks = [task for task in tasks if task[0] != 'predictBinding']
    if not inspire_settings['pathogen']:
        tasks = [task for task in tasks if task[0] != 'extractCandidates']
    if not inspire_settings['quantify']:
        tasks = [task for task in tasks if task[0] != 'quantify']

    task_ids = [task[0] for task in tasks]
    task_names = [task[1] for task in tasks]
    task_df = pd.DataFrame({
        'taskId': task_ids,
        'taskName': task_names
    })
    task_df['taskIndex'] = task_df.index + 1
    task_df['status'] = 'Queued'
    task_df.to_csv(f'{project_home}/taskStatus.csv', index=False)

def create_status_fig(project_home):
    if not os.path.exists(f'{project_home}/taskStatus.csv'):
        return
    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    task_colors = []
    for idx in range(3):
        task_colors.append([])
        for task_status in task_df['status'].tolist():
            if task_status == 'Queued':
                task_colors[idx].append('#AFEEEE')
            if task_status == 'Completed':
                task_colors[idx].append('darkseagreen')
            if task_status == 'Failed':
                task_colors[idx].append('lightcoral')
            if task_status == 'Running':
                task_colors[idx].append('#FFE4B5')
            if task_status == 'Skipped':
                task_colors[idx].append('#FFE4B5')
            if task_status == 'Job Cancelled':
                task_colors[idx].append('#dec8d1')

    fig = go.Figure(
        data=[
            go.Table(
                header={
                    'height': 25,
                    'values': [
                        'Task Index',
                        'Task',
                        'Task Status',
                    ],
                    'line_color': 'black',
                    'align': 'left',
                },
                cells={
                    'height': 20,
                    'values': [
                        task_df.taskIndex,
                        task_df.taskName,
                        task_df.status,
                    ],
                    'fill_color': task_colors,
                    'line_color': 'black',
                    'align': 'left',
                },
                columnwidth = [120,200,120],
            )
        ]
    )
    total_height = (task_df.shape[0]*20) + 25 + 4
    padding = (300 - total_height)/2
    fig.update_layout(
        width=500,
        height=300,
        margin=dict(r=30, l=30, t=padding, b=padding)
    )

    fig_html = fig.to_html()
    fig.write_image(
        f'{project_home}/progress.svg', engine='kaleido'
    )
    with open(
        f'{project_home}/progress.html',
        mode='w',
        encoding='UTF-8',
    ) as html_out:
        html_out.write(fig_html)



def create_queue_fig(project_home):
    queue_df = pd.read_csv('locks/inspireQueue.csv')
    queue_length = queue_df.shape[0]
    task_colors = []
    for idx in range(4):
        task_colors.append([])
        for row_idx in range(queue_length):
            if row_idx > 0:
                task_colors[idx].append('#AFEEEE')
            else:
                task_colors[idx].append('#FFE4B5')

    fig = go.Figure(
        data=[
            go.Table(
                header={
                    'height': 25,
                    'values': [
                        'User',
                        'Project',
                        'Task ID',
                        'Task Status',
                    ],
                    'line_color': 'black',
                    'align': 'left',
                },
                cells={
                    'height': 20,
                    'values': [
                        queue_df.user,
                        queue_df.project,
                        queue_df.taskID,
                        queue_df.status,
                    ],
                    'fill_color': task_colors,
                    'line_color': 'black',
                    'align': 'left',
                },
                columnwidth = [200, 200, 100, 300],
            )
        ]
    )
    total_height = (queue_df.shape[0]*20) + 25 + 4
    # padding = (300 - total_height)/2
    fig.update_layout(
        width=800,
        height=total_height+20,
        margin=dict(r=30, l=30, t=10, b=10)
    )

    fig.write_image(f'{project_home}/queue.svg', engine='kaleido')
