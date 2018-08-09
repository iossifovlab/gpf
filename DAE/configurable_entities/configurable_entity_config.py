from box import ConfigBox
import os
import reusables


class ConfigurableEntityConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(ConfigurableEntityConfig, self).__init__(*args, **kwargs)

    @staticmethod
    def get_config(config_file, work_dir, default_settings, work_dir_key):
        if work_dir is None:
            work_dir = default_settings.DATA_DIR
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
