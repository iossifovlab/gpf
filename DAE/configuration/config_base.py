import os

from configparser import ConfigParser
from box import ConfigBox
from collections import OrderedDict


class CaseSensitiveConfigParser(ConfigParser):
    """
    Modified ConfigParser that allows case sensitive options.
    """

    def optionxform(self, option):
        """
        The default implementation returns a lower-case version of options.
        """
        return str(option)


class ConfigBase(object):

    NEW_KEYS_NAMES = {}
    CONCAT_OPTIONS = {}
    SPLIT_STR_LISTS = ()
    SPLIT_STR_SETS = ()
    CAST_TO_BOOL = ()
    CAST_TO_INT = ()
    ELEMENTS_TO_COPY = {}

    def __init__(self, config, *args, **kwargs):
        super(ConfigBase, self).__init__(*args, **kwargs)
        self.config = ConfigBox(config, camel_killer_box=True)

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
            return super(ConfigBase, self).__getattr__(key)
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
                super(ConfigBase, self).__setattr__(key, value)
        return self.config.__setattr__(key, value)

    def __delitem__(self, key):
        return self.config.__delitem__(key)

    def __delattr__(self, item):
        return self.config.__delattr__(item)

    def __iter__(self):
        return self.config.__iter__()

    def to_dict(self):
        return self.config.to_dict()

    @classmethod
    def read_config(
            cls, config_file, work_dir, default_values=None,
            default_conf=None):
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
            strict=True)

        # print("READING CONFIG FROM '", config_file, "'", file=sys.stderr)
        # print("traceback: ---------------------------------------------")
        # traceback.print_stack(file=sys.stderr)
        # print("traceback: ---------------------------------------------")

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

    @classmethod
    def parse(cls, config_section):
        config_section = cls._change_keys_names(config_section)
        config_section = cls._concat_two_options(config_section)
        config_section = cls._split_str_lists(config_section)
        config_section = cls._split_str_sets(config_section)
        config_section = cls._cast_to_bool(config_section)
        config_section = cls._cast_to_int(config_section)
        config_section = cls._copy_elements(config_section)

        return config_section

    @classmethod
    def add_default_config_key_from_section(cls, config_section, section,
                                            config_key):
        if config_key not in config_section:
            config_section[config_key] = section

    @staticmethod
    def _str_to_bool(val):
        true_values = ['yes', 'Yes', 'True', 'true']
        return True if val in true_values else False

    @classmethod
    def _change_keys_names(cls, config):
        for old, new in cls.NEW_KEYS_NAMES.items():
            if '.' in new and (
                (new.split('.')[0] in config and
                 config.get(new.split('.')[0], None) == 'no') or
                    (config.get(old.split('.')[0], None) == 'no')):
                continue
            if old in config:
                config[new] = config.pop(old)

        return config

    @staticmethod
    def _split_str_option_list(str_option):
        if str_option is not None and str_option != '':
            return [el.strip() for el in str_option.split(',')]
        elif str_option == '':
            return []
        else:
            return []

    @classmethod
    def _split_str_lists(cls, config):
        for key in cls.SPLIT_STR_LISTS:
            if key not in config:
                continue
            config[key] = cls._split_str_option_list(config[key])

        return config

    @classmethod
    def _split_str_sets(cls, config):
        for key in cls.SPLIT_STR_SETS:
            if key not in config:
                continue
            config[key] = set(cls._split_str_option_list(config[key]))

        return config

    @classmethod
    def _cast_to_bool(cls, config):
        for key in cls.CAST_TO_BOOL:
            if key in config:
                config[key] = cls._str_to_bool(config[key])

        return config

    @classmethod
    def _cast_to_int(cls, config):
        for key in cls.CAST_TO_INT:
            if key in config:
                config[key] = int(config[key])

        return config

    @classmethod
    def _concat_two_options(cls, config):
        for first, second in cls.CONCAT_OPTIONS.items():
            res =\
                ','.join(filter(None, [config.pop(first, None),
                                       config.pop(second, None)]))
            if res:
                config[second] = res
        return config

    @classmethod
    def _copy_elements(cls, config):
        for old, new in cls.ELEMENTS_TO_COPY.items():
            config[new] = config[old]

        return config

    @staticmethod
    def _split_section(section):
        index = section.find('.')
        if index == -1:
            return (section, None)
        section_type = section[:index]
        section_name = section[index + 1:]
        return (section_type, section_name)

    @classmethod
    def _get_selectors(
            cls, config, selector_group, selector_getter,
            selector_elements=None):
        selector = OrderedDict()
        for key, value in config.items():
            option_type, option_fullname = cls._split_section(key)
            if (option_type != selector_group and selector_group is not None) \
                    or option_fullname is None:
                continue

            if selector_elements is not None:
                ot, of = cls._split_section(option_fullname)
                if of is None:
                    if option_type not in selector_elements:
                        continue
                else:
                    if ot not in selector_elements:
                        continue

            selector_key = ''
            if selector_group is not None:
                selector_type, selector_option =\
                    cls._split_section(option_fullname)
                selector_key = selector_group + '.' + selector_type
            else:
                selector_type, selector_option = option_type, option_fullname
                selector_key = selector_type

            if selector_key not in selector:
                selector[selector_key] = [selector_option]
            else:
                selector[selector_key].append(selector_option)

        selectors = []
        for selector_type, selector_options in selector.items():
            for s in selector_getter(selector_type, selector_options, config):
                selectors.append(s)

        return selectors
