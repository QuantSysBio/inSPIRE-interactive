""" Definition of Config class.
"""
import yaml

from inspire_interact.constants import (
    ALL_CONFIG_KEYS,
    FILESERVER_NAME_KEY,
    THERMO_PARSER_KEY,
)

class Config:
    """ Holder for configuration of the inspire pipeline.
    """
    def __init__(self, config_file):
        with open(config_file, 'r', encoding='UTF-8') as stream:
            config_dict = yaml.safe_load(stream)
        for config_key in config_dict:
            if config_key not in ALL_CONFIG_KEYS:
                raise ValueError(f'Unrecognised key {config_key} found in config file.')
        self._load_data(config_dict)


    def _load_data(self, config_dict):
        """ Function to load data.
        """
        self.fileserver_name = config_dict.get(FILESERVER_NAME_KEY, None)
        self.thermo_parser = config_dict.get(THERMO_PARSER_KEY, None)
