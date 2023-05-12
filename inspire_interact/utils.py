""" Utility functions for inSPIRE-interact.
"""
import os

import yaml
from inspire_interact.constants import (
    CPUS_KEY,
    FRAGGER_MEMORY_KEY,
    FRAGGER_PATH_KEY,
)
#TODO: break up into small functions, readability issues
def prepare_inspire(config_dict, project_home, app_config):
    """ Function to prepare the inSPIRE run.
    """
    inspire_settings = {
        'convert': False,
        'fragger': False,
        'select': False,
    }
    inspire_settings['quantify'] = bool(config_dict['runQuantification'])

    output_config = {
        'experimentTitle': config_dict['project'],
        'searchEngine': config_dict['searchEngine'],
        'scansFormat': 'mgf',
        'outputFolder': f'{project_home}/inspireOutput',
        'mzAccuracy': float(config_dict['mzAccuracy']),
        'mzUnits': config_dict['mzUnits'],
        'rescoreMethod': 'percolator',
        'silentExecution': True,
        'reuseInput': True,
        'fraggerPath': app_config[FRAGGER_PATH_KEY],
        'fraggerMemory': app_config[FRAGGER_MEMORY_KEY],
        'nCores': app_config[CPUS_KEY]
    }

    if config_dict['runFragger'] == 1:
        inspire_settings['fragger'] = True
    else:
        output_config['searchResults'] = [
            f'{project_home}/search/{filename}' for filename in os.listdir(
                f'{project_home}/search/'
            )
        ]

    output_config['scansFolder'] = f'{project_home}/ms'

    ms_files = os.listdir(f'{project_home}/ms')
    if ms_files[0].lower().endswith('.raw'):
        inspire_settings['convert'] = True

    if config_dict['searchEngine'] in ('mascot', 'msfragger'):
        output_config['rescoreMethod'] = 'percolator'
    else:
        output_config['rescoreMethod'] = 'percolatorSeparate'

    
    if os.path.exists(f'{project_home}/proteome'):
        proteome_files = os.listdir(f'{project_home}/proteome')
        prot_file_name = proteome_files[0]
        output_config['proteome'] = f'{project_home}/proteome/{prot_file_name}'
    else:
        proteome_files = os.listdir(f'{project_home}/proteome-select')
        inspire_settings['select'] = True
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
            elem.strip() for elem in  config_dict["controlFlags"].split(",")
        ]

    with open(f'{project_home}/config.yml', 'w', encoding='UTF-8') as yaml_out:
        yaml.dump(output_config, yaml_out)

    return inspire_settings


def check_pids(project_home, workflow):
    """ Function to check if process IDs are still running.
    """
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
