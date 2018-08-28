from box import ConfigBox
import os
import reusables
from ConfigParser import ConfigParser
from box import Box

import common.config


class ConfigurableEntityConfig(Box):

    def __init__(self, *args, **kwargs):
        super(ConfigurableEntityConfig, self).__init__(*args, **kwargs)

    @staticmethod
    def get_config(config_file, work_dir, default_values={}):
        if not os.path.exists(config_file):
            config_file = os.path.join(work_dir, config_file)
        assert os.path.exists(config_file), config_file

        default_values['work_dir'] = work_dir

        config = reusables.config_dict(
            config_file,
            auto_find=False,
            verify=True,
            defaults=default_values
        )

        return config

    @classmethod
    def add_default_config_key_from_section(cls, config_section, section,
                                            config_key):
        if config_key not in config_section:
            config_section[config_key] = section
