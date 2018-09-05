from box import ConfigBox
import os
from ConfigParser import ConfigParser


class MyConfigParser(ConfigParser):

    def optionxform(self, option):
        return str(option)


class ConfigurableEntityConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(ConfigurableEntityConfig, self).__init__(*args, **kwargs)

    @staticmethod
    def get_config(config_file, work_dir, default_values={}):
        if not os.path.exists(config_file):
            config_file = os.path.join(work_dir, config_file)
        assert os.path.exists(config_file), config_file

        default_values['work_dir'] = work_dir

        config_parser = MyConfigParser(defaults=default_values)
        config_parser.read(config_file)

        config = dict((section, dict(config_parser.items(section)))
                      for section in config_parser.sections())

        return config

    @classmethod
    def add_default_config_key_from_section(cls, config_section, section,
                                            config_key):
        if config_key not in config_section:
            config_section[config_key] = section

    @staticmethod
    def _str_to_bool(val):
        true_values = ['yes', 'Yes', 'True', 'true']
        return True if val in true_values else False

    @staticmethod
    def _change_keys_names(new_keys_names, config):
        for old, new in new_keys_names.items():
            if '.' in new and (
                (new.split('.')[0] in config and
                 config.get(new.split('.')[0], None) == 'no') or
                    (config.get(old.split('.')[0], None) == 'no')):
                continue
            if old in config:
                config[new] = config.pop(old)

        return config

    @staticmethod
    def _split_str_lists(split_str_lists_keys, config):
        for key in split_str_lists_keys:
            if key not in config:
                continue
            if config[key] is not None and config[key] != '':
                config[key] =\
                    set([el.strip() for el in config[key].split(',')])
            elif config[key] == '':
                config[key] = []

        return config

    @classmethod
    def _cast_to_bool(cls, cast_to_bool_keys, config):
        for key in cast_to_bool_keys:
            if key in config:
                config[key] = cls._str_to_bool(config[key])

        return config
