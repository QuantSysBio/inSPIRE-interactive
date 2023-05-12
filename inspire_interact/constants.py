""" Constants for the inspire_interact package.
"""
FILESERVER_NAME_KEY = 'fileserverName'
INTERACT_HOME_KEY = 'interactHome'
SERVER_ADDRESS_KEY = 'serverAddress'
FRAGGER_PATH_KEY = 'fraggerPath'
FRAGGER_MEMORY_KEY = 'fraggerMemory'
CPUS_KEY = 'maxInspireCpus'
MHCPAN_KEY = 'netMHCpan'
MODE_KEY = 'mode'

ALL_CONFIG_KEYS = [
    CPUS_KEY,
    FILESERVER_NAME_KEY,
    FRAGGER_PATH_KEY,
    FRAGGER_MEMORY_KEY,
    INTERACT_HOME_KEY,
    MHCPAN_KEY,
    SERVER_ADDRESS_KEY,
]

INTERMEDIATE_FILES = [
    # 'input_all_features.tab'
]