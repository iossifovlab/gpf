from box import ConfigBox
import os
from ConfigParser import ConfigParser


class MyConfigParser(ConfigParser):

    def optionxform(self, option):
        return str(option)


class ConfigurableEntityConfig(object):

    def __init__(self, config, *args, **kwargs):
        super(ConfigurableEntityConfig, self).__init__(*args, **kwargs)
        self.config = ConfigBox(config)

    def bool(self, item, default=None):
        return self.config.bool(item, default=default)

    def int(self, item, default=None):
        return self.config.int(item, default=default)

    def float(self, item, default=None):
        return self.config.float(item, default=default)

    def list(self, item, default=None, spliter=",", strip=True, mod=None):
        return self.config.list(
            item, default=default, spliter=spliter, strip=strip, mod=mod)

    def __getitem__(self, key):
        return self.config.__getitem__(key)

    def __getattr__(self, key):
        if key == 'config':
            return super(ConfigurableEntityConfig, self).__getattr__(key)
        return self.config.__getattr__(key)

    def __contains__(self, key):
        return self.config.__contains__(key)

    def __str__(self):
        return self.config.__str__()

    def __repr__(self):
        return self.config.__repr__()

    def __hash__(self):
        return self.config.__hash__()

    def keys(self):
        return self.config.keys()

    def values(self):
        return self.config.values()

    def items(self):
        return self.config.items()

    def __setitem__(self, key, value):
        return self.config.__setitem__(key, value)

    def __setattr__(self, key, value):
        if key == 'config':
            return\
                super(ConfigurableEntityConfig, self).__setattr__(key, value)
        return self.config.__setattr__(key, value)

    def __delitem__(self, key):
        return self.config.__delitem__(key)

    def __delattr__(self, item):
        return self.config.__delattr__(item)

    def __iter__(self):
        return self.config.__iter__()

    def to_dict(self):
        return self.config.to_dict()

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
