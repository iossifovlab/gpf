import os
from collections import OrderedDict
from configparser import ConfigParser


class CaseSensitiveConfigParser(ConfigParser):
    """
    Modified ConfigParser that allows case sensitive options.
    """

    def optionxform(self, option):
        """
        The default implementation returns a lower-case version of options.
        """
        return str(option)


class DAEConfigParser(object):

    ENABLED_DIR = '.'

    @classmethod
    def directory_configurations(
            cls, configurations_dir, config_class, work_dir,
            default_values=None, default_conf=None, fail_silently=False,
            enabled_dir='.'):
        if default_values is None:
            default_values = {}
        assert isinstance(configurations_dir, str),\
            type(configurations_dir)

        enabled_dir = os.path.join(configurations_dir, enabled_dir)
        enabled_dir = os.path.abspath(enabled_dir)

        configs = []
        config_paths = cls._collect_config_paths(enabled_dir, fail_silently)

        for config_path in config_paths:
            config = cls.load_config(
                config_path, enabled_dir, config_class, default_values,
                default_conf)

            if config:
                configs.append(config)

        configs = {config.id: config for config in configs}

        return configs

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

    @classmethod
    def single_file_configuration(
            cls, config_path, work_dir, config_class, default_values=None,
            default_conf=None):
        if default_values is None:
            default_values = {}

        config = DAEConfigParser.load_config(
            config_path, work_dir, config_class, default_values, default_conf)

        if config and 'id' in config:
            configs = {config.id: config}
        else:
            configs = config

        return configs

    @classmethod
    def load_config(
            cls, config_file, work_dir, config_class, default_values=None,
            default_conf=None):
        if default_values is None:
            default_values = {}

        config = cls.read_config(
            config_file, work_dir, default_values, default_conf)
        config['config_file'] = config_file
        entity_config = config_class.from_config(config)

        return entity_config

    @staticmethod
    def read_config(
            config_file, work_dir, default_values=None, default_conf=None):
        if default_values is None:
            default_values = {}

        if not os.path.exists(config_file):
            config_file = os.path.join(work_dir, config_file)
        assert os.path.exists(config_file), config_file

        default_values['work_dir'] = work_dir
        default_values['wd'] = work_dir

        config_parser = CaseSensitiveConfigParser(
            defaults=default_values,
            allow_no_value=True,
            strict=True
        )

        if default_conf is not None:
            assert os.path.exists(default_conf)
            with open(default_conf, 'r') as f:
                config_parser.read_file(f)

        with open(config_file, 'r') as f:
            config_parser.read_file(f)

        config = OrderedDict(
            (section, OrderedDict(config_parser.items(section)))
            for section in config_parser.sections())

        return config
