""" Functions for executing inSPIRE within inSPIRE-interactive.
"""
import ast
import os

import yaml

from inspire_interact.constants import (
    CPUS_KEY,
    FRAGGER_MEMORY_KEY,
    FRAGGER_PATH_KEY,
    INTERACT_HOME_KEY,
    MHCPAN_KEY,
)
from inspire_interact.utils import write_task_status, subset_tasks

def execute_inspire(app_config, project_home, user, project, config_dict):
    """ Function to execute inSPIRE, writes config file, a bash file with all
        required tasks, and then executes the bash file in the background.
    """
    inspire_settings = prepare_inspire(config_dict, project_home, app_config)
    write_task_status(inspire_settings, project_home)

    write_inspire_script(
        app_config[INTERACT_HOME_KEY],
        project_home,
        user,
        project,
        inspire_settings,
    )

    # In case of rerunning, we should be careful not to reuse this file.
    if os.path.exists(f'{project_home}/inspireOutput/formated_df.csv'):
        os.remove(f'{project_home}/inspireOutput/formated_df.csv')

    os.system(
        f'bash {project_home}/inspire_script.sh > {project_home}/inspire_log.txt 2>&1 &',
    )


def write_inspire_task(bash_file, project_home, task, interact_home):
    """ Function to write a task to be executed by inSPIRE - both the command
        and clean up in the case of failure.
    """
    bash_file.write(
        f'inspire --pipeline {task} --config_file {project_home}/config.yml\n'
    )
    bash_file.write(
        f'interact-queue --project_home {project_home} ' +
        f' --interact_home {interact_home}' +
        f' --queue_task update --inspire_task {task} --inspire_status $?\n'
    )

    # Some tasks do not need to block execution:
    if task not in ('predictBinding', 'quantify', 'generateReport'):
        bash_file.write(
            'if [ "$?" -ne "0" ]\n' +
            '  then\n' +
            f'    interact-queue --project_home {project_home} --interact_home {interact_home} ' +
            ' --queue_task remove\n' +
            '    exit 0\n' +
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

def write_inspire_script(home_key, project_home, user, project, inspire_settings):
    """ Function to write bash file with inSPIRE execution.
    """
    with open(
        f'projects/{user}/{project}/inspire_script.sh',
        'w',
        encoding='UTF-8'
    ) as bash_file:
        bash_file.write(
            f'echo $$ > {project_home}/inspire_pids.txt ;\n'
        )
        for additional_settings in (
            'add',
            'check',
            'update --inspire_task start --inspire_status 0'
        ):
            bash_file.write(
                f'interact-queue --project_home {project_home} --interact_home {home_key} ' +
                f' --queue_task {additional_settings}\n'
            )

        tasks = subset_tasks(inspire_settings)
        for task in tasks:
            write_inspire_task(bash_file, project_home, task, home_key)

        bash_file.write(
            f'interact-queue --project_home {project_home} ' +
            f' --interact_home {home_key} ' +
            ' --queue_task remove\n'
        )
