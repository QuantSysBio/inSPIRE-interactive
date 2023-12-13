""" Constants for the inspire_interact package.
"""
INTERACT_HOME_KEY = 'interactHome'
SERVER_ADDRESS_KEY = 'serverAddress'
FRAGGER_PATH_KEY = 'fraggerPath'
FRAGGER_MEMORY_KEY = 'fraggerMemory'
CPUS_KEY = 'maxInspireCpus'
MHCPAN_KEY = 'netMHCpan'
MODE_KEY = 'mode'
SKYLINE_RUNNER_KEY = 'skylineRunner'

QUEUE_PATH = '{home_key}/locks/inspireQueue.csv'

ALL_CONFIG_KEYS = [
    CPUS_KEY,
    FRAGGER_PATH_KEY,
    FRAGGER_MEMORY_KEY,
    INTERACT_HOME_KEY,
    MHCPAN_KEY,
    SERVER_ADDRESS_KEY,
    SKYLINE_RUNNER_KEY,
]

INTERMEDIATE_FILES = [
    # 'input_all_features.tab'
]

KEY_FILES = {
    'epitopePlots': 'inspireOutput/epitope/spectralPlots.pdf',
    'epitopeReport': 'inspireOutput/epitope/inspire-epitope-report.html',
    'inspire': 'inspireOutput/finalPsmAssignments.csv',
    'inspireLog': 'inspire_log.txt',
    'inspirePathogen': 'inspireOutput/epitope/potentialEpitopeCandidates.xlsx',
    'performance': 'inspireOutput/inspire-report.html',
    'quantification': 'inspireOutput/quant.zip',
    'quantReport': 'inspireOutput/quant/inspire-quant-report.html',
}

TASKS_NAMES = [
    'convert',
    'fragger',
    'prepare',
    'predictSpectra',
    'predictBinding',
    'featureGeneration',
    'featureSelection+',
    'generateReport',
    'quantify',
    'extractCandidates',
]
TASK_DESCRIPTIONS = {
    'convert': 'Converting MS Data',
    'fragger': 'Executing MSFragger',
    'prepare': 'Preparing results',
    'predictSpectra': 'Predicting spectra',
    'predictBinding': 'Predicting binding',
    'featureGeneration': 'Generating features',
    'featureSelection+': 'Executing rescoring',
    'generateReport': 'Creating report',
    'quantify': 'Quantifying peptides',
    'extractCandidates': 'Finding pathogen peptides',
}
