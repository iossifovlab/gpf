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
            self, configurable_entities_dir, configurable_entity_config,
            config_key):
        assert isinstance(configurable_entities_dir, str),\
            type(configurable_entities_dir)
        assert os.path.exists(configurable_entities_dir),\
            configurable_entities_dir

        enabled_dir = os.path.join(configurable_entities_dir, self.ENABLED_DIR)
        assert os.path.exists(enabled_dir), enabled_dir
        assert os.path.isdir(enabled_dir), enabled_dir

        config_paths = []
        configs = []

        for path in os.listdir(enabled_dir):
            if not os.path.isdir(path) and path.endswith('.conf'):
                config_paths.append(os.path.join(enabled_dir, path))

        print(config_paths)

        for config_path in config_paths:
            configs.append(configurable_entity_config.from_config(config_path))

        self.configs = {conf[config_key]: conf for conf in configs}

    def single_file_configurable_entity_definition(
            self, config_path, work_dir, configurable_entity_config,
            config_key):
        self.config_path = config_path

        config = configurable_entity_config.from_config(config_path, work_dir)

        self.configs = {
            config[config_key]: config
        }

        print(self.configs)

    @classmethod
    def list_from_config(cls, config_file, work_dir,
                         configurable_entity_config, config_key):
        config = configurable_entity_config.get_config(config_file, work_dir)

        result = list()
        for section in config.keys():
            config_section =\
                configurable_entity_config.from_config(config[section])

            cls.add_default_config_key_from_section(config_section, section,
                                                    config_key)

            result.append(configurable_entity_config(config[section]))

        return result

    @classmethod
    def add_default_config_key_from_section(cls, config_section, section,
                                            config_key):
        if config_key not in config_section:
            config_section[config_key] = section

    @classmethod
    def get_definition_from_config(
            cls, config_file, work_dir, configurable_entity_config,
            configurable_entity_definition, config_key):
        print("from_config_file", work_dir, config_file)

        configs = cls.list_from_config(
            config_file, work_dir, configurable_entity_config,
            config_key)

        definition = configurable_entity_definition()

        definition.configs = {
            config[config_key]: config
            for config in configs
        }

        return definition
