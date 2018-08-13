from box import ConfigBox
import os
import reusables


class ConfigurableEntityConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(ConfigurableEntityConfig, self).__init__(*args, **kwargs)

    @staticmethod
    def get_config(config_file, work_dir):
        if not os.path.exists(config_file):
            config_file = os.path.join(work_dir, config_file)
        assert os.path.exists(config_file), config_file

        config = reusables.config_dict(
            config_file,
            auto_find=False,
            verify=True,
            defaults={
                'work_dir': work_dir,
            }
        )

        return config

    @classmethod
    def add_default_config_key_from_section(cls, config_section, section,
                                            config_key):
        if config_key not in config_section:
            config_section[config_key] = section
