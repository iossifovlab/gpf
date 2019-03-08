from __future__ import unicode_literals
from builtins import str

import os
import abc


class ConfigurableEntityDefinition(object):
    __metaclass__ = abc.ABCMeta
    ENABLED_DIR = '.'

    # configs = {}

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
            self, configurable_entities_dir, configurable_entity_config_class,
            work_dir, default_values={}, default_conf=None):
        assert isinstance(configurable_entities_dir, str),\
            type(configurable_entities_dir)
        assert os.path.exists(configurable_entities_dir),\
            configurable_entities_dir

        enabled_dir = os.path.join(configurable_entities_dir, self.ENABLED_DIR)
        enabled_dir = os.path.abspath(enabled_dir)

        assert os.path.exists(enabled_dir), enabled_dir
        assert os.path.isdir(enabled_dir), enabled_dir

        configs = []
        config_paths =\
            ConfigurableEntityDefinition._collect_config_paths(enabled_dir)

        for config_path in config_paths:
            config = ConfigurableEntityDefinition.load_entity_config(
                config_path, enabled_dir, configurable_entity_config_class,
                default_values, default_conf)

            if config:
                configs.append(config)

        self.configs = {config.id: config for config in configs}

    @classmethod
    def _collect_config_paths(cls, dirname):
        config_paths = []
        for path in os.listdir(dirname):
            p = os.path.join(dirname, path)
            if os.path.isdir(p):
                subpaths = cls._collect_config_paths(p)
                config_paths.extend(subpaths)
            elif path.endswith('.conf'):
                config_paths.append(
                    os.path.join(dirname, path)
                )
        return config_paths

    def single_file_configurable_entity_definition(
            self, config_path, work_dir, configurable_entity_config_class,
            default_values={}, default_conf=None):
        self.config_path = config_path

        config = ConfigurableEntityDefinition.load_entity_config(
            config_path, work_dir, configurable_entity_config_class,
            default_values, default_conf)

        if config and id in config:
            self.configs = {config.id: config}
        else:
            self.configs = config

    @classmethod
    def load_entity_config(
            cls, config_file, work_dir, configurable_entity_config_class,
            default_values={}, default_conf=None):
        config = configurable_entity_config_class.read_config(
            config_file, work_dir, default_values, default_conf)
        config['config_file'] = config_file
        entity_config = configurable_entity_config_class.from_config(config)

        return entity_config
