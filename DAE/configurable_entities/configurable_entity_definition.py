from __future__ import unicode_literals
from builtins import str

import os
import abc
from itertools import chain


class ConfigurableEntityDefinition(object):
    __metaclass__ = abc.ABCMeta

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
            self, configurable_entities_dir, configurable_entity_config,
            work_dir, config_key, default_values={}):
        assert isinstance(configurable_entities_dir, str),\
            type(configurable_entities_dir)
        assert os.path.exists(configurable_entities_dir),\
            configurable_entities_dir

        enabled_dir = os.path.join(configurable_entities_dir, self.ENABLED_DIR)
        enabled_dir = os.path.abspath(enabled_dir)

        assert os.path.exists(enabled_dir), enabled_dir
        assert os.path.isdir(enabled_dir), enabled_dir

        configs = []
        config_paths = self._collect_config_paths(enabled_dir)

        for config_path in config_paths:

            configs.append(ConfigurableEntityDefinition.list_from_config(
                config_path, enabled_dir, configurable_entity_config,
                default_values))

        configs = list(chain.from_iterable(configs))

        self.configs = {conf[config_key]: conf for conf in configs}

    def _collect_config_paths(self, dirname):
        config_paths = []
        for path in os.listdir(dirname):
            p = os.path.join(dirname, path)
            if os.path.isdir(p):
                subpaths = self._collect_config_paths(p)
                config_paths.extend(subpaths)
            elif path.endswith('.conf'):
                config_paths.append(
                    os.path.join(dirname, path)
                )
        return config_paths

    def single_file_configurable_entity_definition(
            self, config_path, work_dir, configurable_entity_config,
            config_key, default_values={}):
        self.config_path = config_path

        configs = ConfigurableEntityDefinition.list_from_config(
            config_path, work_dir, configurable_entity_config, default_values)

        self.configs = {
            config[config_key]: config
            for config in configs
        }

    @classmethod
    def list_from_config(cls, config_file, work_dir,
                         configurable_entity_config, default_values={}):
        config = configurable_entity_config.get_config(
            config_file, work_dir, default_values)

        result = list()
        for section in config.keys():

            entity_config = configurable_entity_config.from_config(
                config[section])

            if entity_config is not None:
                entity_config['section_name'] = section
                result.append(entity_config)

        return result
