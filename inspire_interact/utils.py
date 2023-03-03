""" Utility functions for inSPIRE-interact.
"""
import os

import yaml

def prepare_inspire(config_dict, project_home, fragger_path, fragger_memory):
    """ Function to prepare the inSPIRE run.
    """
    inspire_settings = {
        'convert': False,
        'fragger': False,
        'select': False,
    }

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
        'fraggerPath': fragger_path,
        'fraggerMemory': fragger_memory,
    }

    if os.path.exists(f'{project_home}/search_file_list.txt'):
        with open(
            f'{project_home}/search_file_list.txt', mode='r', encoding='UTF-8'
        ) as list_file:
            file_list = list_file.readlines()
            output_config['searchResults'] = [x.split()[-1].split('\n')[0] for x in file_list]
    elif config_dict['runFragger'] == 1:
        inspire_settings['fragger'] = True
    else:
        output_config['searchResults'] = [
            f'{project_home}/search/{filename}' for filename in os.listdir(
                f'{project_home}/search/'
            )
        ]

    if os.path.exists(f'{project_home}/ms_file_list.txt'):
        with open(
            f'{project_home}/ms_file_list.txt', mode='r', encoding='UTF-8'
        ) as list_file:
            file_list = list_file.readlines()
            output_config['scansFiles'] = [x.split()[-1].split('\n')[0] for x in file_list]
    else:
        output_config['scansFolder'] = f'{project_home}/ms'

    ms_files = os.listdir(f'{project_home}/ms')
    if ms_files[0].lower().endswith('.raw'):
        inspire_settings['convert'] = True


    if config_dict['searchEngine'] in ('mascot', 'msfragger'):
        output_config['rescoreMethod'] = 'percolator'
    else:
        output_config['rescoreMethod'] = 'percolatorSeparate'

    if os.path.exists(f'{project_home}/proteome_file_list.txt'):
        with open(
            f'{project_home}/proteome_file_list.txt', mode='r', encoding='UTF-8'
        ) as list_file:
            file_list = list_file.readlines()
            output_config['proteome'] = [x.split()[-1].split('\n')[0] for x in file_list][0]
    elif not inspire_settings['select']:
        output_config['proteome'] = f'{project_home}/proteome/proteome.fasta'

    if os.path.exists(f'{project_home}/proteome/pathogenProteome.fasta'):
        output_config['pathogenProteome'] = f'{project_home}/proteome/pathogenProteome.fasta'
        output_config['hostProteome'] = f'{project_home}/proteome/hostProteome.fasta'
        # TODO control flags.
    elif os.path.exists(f'{project_home}/proteomeSelect_file_list.txt'):
        with open(
            f'{project_home}/proteome_file_list.txt', mode='r', encoding='UTF-8'
        ) as list_file:
            file_list = list_file.readlines()
            proteome_files = [x.split()[-1].split('\n')[0] for x in file_list]
            output_config['hostProteome'] = proteome_files[0]
            output_config['pathogenProteome'] = proteome_files[1]

    with open(f'{project_home}/config.yml', 'w', encoding='UTF-8') as yaml_out:
        yaml.dump(output_config, yaml_out)

    if (
        os.path.exists(f'{project_home}/proteome/pathogenProteome.fasta') or
        os.path.exists(f'{project_home}/proteomeSelect_file_list.txt')
    ):
        inspire_settings['select'] = True

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
