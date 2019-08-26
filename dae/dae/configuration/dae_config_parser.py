import os
from box import Box
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

    SECTION = None

    SPLIT_STR_LISTS = ()
    SPLIT_STR_SETS = ()
    CAST_TO_BOOL = ()
    CAST_TO_INT = ()
    PARSE_TO_LIST = {}
    CONVERT_LIST_TO_DICT = ()

    @classmethod
    def read_and_parse_directory_configurations(
            cls, configurations_dir, work_dir, defaults=None,
            fail_silently=False):
        if defaults is None:
            defaults = {}

        configs = cls.read_directory_configurations(
            configurations_dir, work_dir, defaults=defaults,
            fail_silently=fail_silently
        )

        parsed_configs = []

        for config in configs:
            parsed_config = cls.parse(config)
            parsed_configs.append(parsed_config)

        return parsed_configs

    @classmethod
    def read_and_parse_file_configuration(
            cls, config_file, work_dir, defaults=None):
        if defaults is None:
            defaults = {}

        config = cls.read_file_configuration(
            config_file, work_dir, defaults=defaults
        )

        config = cls.parse(config)

        return config

    @classmethod
    def read_directory_configurations(
            cls, configurations_dir, work_dir, defaults=None,
            fail_silently=False):
        if defaults is None:
            defaults = {}

        assert isinstance(configurations_dir, str), type(configurations_dir)

        enabled_dir = os.path.join(configurations_dir, cls.ENABLED_DIR)
        enabled_dir = os.path.abspath(enabled_dir)

        configs = []
        config_paths = cls._collect_config_paths(enabled_dir, fail_silently)

        for config_path in config_paths:
            config = cls.read_file_configuration(
                config_path, enabled_dir, defaults
            )

            if config:
                configs.append(config)

        return configs

    @classmethod
    def read_file_configuration(cls, config_file, work_dir, defaults=None):
        if defaults is None:
            defaults = {}

        config = cls.read_config(config_file, work_dir, defaults)

        if config is None:
            return None

        config = Box(
            config, camel_killer_box=True, default_box=True,
            default_box_attr=None
        )

        config['config_file'] = config_file

        return config

    @classmethod
    def _collect_config_paths(cls, dirname, fail_silently=False):
        config_paths = []
        print(dirname)
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
    def read_config(cls, config_file, work_dir, defaults=None):
        if defaults is None:
            defaults = {}

        default_values = defaults.get('values', {})
        default_sections = defaults.get('sections', {})
        default_override = defaults.get('override', {})
        default_conf = defaults.get('conf', None)

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

        if default_sections:
            config_parser.read_dict(default_sections)

        if default_conf is not None:
            assert os.path.exists(default_conf)
            with open(default_conf, 'r') as f:
                config_parser.read_file(f)

        with open(config_file, 'r') as f:
            config_parser.read_file(f)

        if default_override:
            config_parser.read_dict(default_override)

        config = OrderedDict(
            (section, OrderedDict(config_parser.items(section)))
            for section in config_parser.sections())

        if cls.SECTION in config:
            if 'enabled' in config[cls.SECTION]:
                if cls._str_to_bool(config[cls.SECTION]['enabled']) is False:
                    return None

        return config

    @classmethod
    def parse(cls, config):
        if not config:
            return None

        sections = list(config.keys())
        if cls.SECTION:
            sections = [cls.SECTION]

        for section in sections:
            config_section = config[section]

            config_section = cls.parse_section(config_section)
            if config_section is None:
                continue

            config[section] = config_section

        return config

    @classmethod
    def parse_section(cls, config_section):
        if config_section is None:
            return None
        if not isinstance(config_section, dict):
            return config_section

        config_section = cls._split_str_lists(config_section)
        config_section = cls._split_str_sets(config_section)
        config_section = cls._cast_to_bool(config_section)
        config_section = cls._cast_to_int(config_section)
        config_section = cls._parse_to_dict(config_section)
        config_section = cls._convert_list_to_dict(config_section)

        return config_section

    @staticmethod
    def _str_to_bool(val):
        true_values = ['yes', 'Yes', 'True', 'true']
        return True if val in true_values else False

    @staticmethod
    def _split_str_option_list(str_option):
        if str_option is not None and str_option != '':
            return [el.strip() for el in str_option.split(',')]
        elif str_option == '':
            return []
        else:
            return []

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
    def _parse_to_dict(cls, config):
        if config is None or not isinstance(config, dict):
            return config

        for key, options in cls.PARSE_TO_LIST.items():
            elements = None
            if 'selected' in options:
                elements = config.get(options['selected'], None)
            selectors = cls._get_selectors(
                config, options['group'], options['getter'], elements
            )

            if selectors:
                config[key] = selectors
            else:
                if 'default' in options:
                    config[key] = options['default']

        return config

    @classmethod
    def _convert_list_to_dict(cls, config):
        for key in cls.CONVERT_LIST_TO_DICT:
            if key in config:
                converted_dict = Box(
                    {el['id']: el for el in config[key] if 'id' in el},
                    camel_killer_box=True, default_box=True,
                    default_box_attr=None
                )
                if len(config[key]) == len(converted_dict):
                    config[key] = converted_dict

        return config
