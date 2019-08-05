import os
import abc


class DAEConfigParser(object):
    __metaclass__ = abc.ABCMeta

    ENABLED_DIR = '.'

    # configs = {}
    def __init__(self):
        self.configs = {}

    @property
    def configurable_entity_ids(self):
        return list(self.configs.keys())

    def get_configurable_entity_config(self, configurable_entity_id):
        if configurable_entity_id not in self.configs:
            return None

        return self.configs[configurable_entity_id]

    def get_all_configurable_entity_configs(self):
        return list(self.configs.values())

    def directory_enabled_configurable_entity_definition(
            self, configurable_entities_dir, configurable_entity_config_class,
            work_dir, default_values=None, default_conf=None,
            fail_silently=False):
        if default_values is None:
            default_values = {}
        assert isinstance(configurable_entities_dir, str),\
            type(configurable_entities_dir)

        enabled_dir = os.path.join(configurable_entities_dir, self.ENABLED_DIR)
        enabled_dir = os.path.abspath(enabled_dir)

        configs = []
        config_paths = DAEConfigParser\
            ._collect_config_paths(enabled_dir, fail_silently)

        for config_path in config_paths:
            config = DAEConfigParser.load_entity_config(
                config_path, enabled_dir, configurable_entity_config_class,
                default_values, default_conf)

            if config:
                configs.append(config)

        self.configs = {config.id: config for config in configs}

    @classmethod
    def _collect_config_paths(cls, dirname, fail_silently=False):
        config_paths = []
        if not os.path.exists(dirname):
            if fail_silently:
                return []
            raise RuntimeError(dirname)
        for path in os.listdir(dirname):
            p = os.path.join(dirname, path)
            if os.path.isdir(p):
                subpaths = cls._collect_config_paths(p, fail_silently)
                config_paths.extend(subpaths)
            elif path.endswith('.conf'):
                config_paths.append(
                    os.path.join(dirname, path)
                )
        return config_paths

    def single_file_configurable_entity_definition(
            self, config_path, work_dir, configurable_entity_config_class,
            default_values=None, default_conf=None):
        if default_values is None:
            default_values = {}

        config = DAEConfigParser.load_entity_config(
            config_path, work_dir, configurable_entity_config_class,
            default_values, default_conf)

        if config and id in config:
            self.configs = {config.id: config}
        else:
            self.configs = config

    @classmethod
    def load_entity_config(
            cls, config_file, work_dir, configurable_entity_config_class,
            default_values=None, default_conf=None):
        if default_values is None:
            default_values = {}
        config = configurable_entity_config_class.read_config(
            config_file, work_dir, default_values, default_conf)
        config['config_file'] = config_file
        entity_config = configurable_entity_config_class.from_config(config)

        return entity_config
