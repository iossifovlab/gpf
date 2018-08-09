import os
import abc


class ConfigurableEntityDefinition(object):
    __metaclass__ = abc.ABCMeta

    configs = {}

    @property
    def configurable_entity_ids(self):
        return list(self.configs.keys())

    def get_configurable_entity_config(self, configurable_entity_id):
        if configurable_entity_id not in self.configs:
            return None

        return self.configs[configurable_entity_id]

    def get_all_configurable_entity_configs(self):
        return list(self.configs.values())

    def get_all_configurable_entity_names(self):
        return list(self.configs.keys())

    def directory_enabled_configurable_entity_definition(
            self, configurable_entities_dir):
        assert isinstance(configurable_entities_dir, str),\
            type(configurable_entities_dir)
        assert os.path.exists(configurable_entities_dir),\
            configurable_entities_dir

        self.configurable_entities_dir = configurable_entities_dir

        enabled_dir = os.path.join(configurable_entities_dir, self.ENABLED_DIR)
        assert os.path.exists(enabled_dir), enabled_dir
        assert os.path.isdir(enabled_dir), enabled_dir

        config_paths = []

        for path in os.listdir(enabled_dir):
            if not os.path.isdir(path) and path.endswith('.conf'):
                config_paths.append(os.path.join(enabled_dir, path))

        print(config_paths)

        self.append_to_config(config_paths)

    def single_file_configurable_entity_definition(
            self, config_path, work_dir):
        self.config_path = config_path

        self.append_to_config(config_path, work_dir)

        print(self.configs)

    @classmethod
    def multiple_files_configurable_entity_definition(
            cls, configs):
        return cls.from_config(configs)
