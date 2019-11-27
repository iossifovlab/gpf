import os
from box import Box
from collections import deque
from configparser import ConfigParser

from dae.configuration.utils import parser_to_dict


class VerificationError(Exception):
    '''
    Exception to raise when there is some verification problem in the
    configuration.

    :param str message: message of the exeption
    :ivar str message: message of the exeption
    '''

    def __init__(self, message):
        self.message = message


class CaseSensitiveConfigParser(ConfigParser):
    '''
    .. _case_sensitive_config_parser:

    Modified `ConfigParser` that allows case sensitive options.
    '''

    def optionxform(self, option):
        '''
        The default implementation returns a lower-case version of options.
        '''
        return str(option)


class ConfigParserBase(object):
    '''
    ConfigParserBase is a base class for all configuration parsers. It is
    responsible for parsing all of the system configuration. It can be
    inherited by a specific parser or be used alone. It has different kinds of
    methods for reading and parsing configurations. Any class which inherits
    from this parser may use its class properties which are used for parsing
    different kinds of properties from the configuration. The return value for
    all of the classmethods for reading a configuration is a Box object. All of
    its methods are class or static methods.
    '''

    ENABLED_DIR = '.'
    '''
    Holds a path, relative to the ``configuration_dir`` parameter, passed in
    :func:`read_directory_configurations` and
    :func:`read_and_parse_directory_configurations` functions. This relative
    path is a directory of the enabled configurations.
    '''

    SECTION = None
    '''
    Holds the name of a configuration section which would be parsed by the
    :func:`parse` function. If it is None, then all of the sections in the
    configuration will be parsed one by one.
    '''

    SPLIT_STR_LISTS = ()
    '''
    Holds a tuple of configuration property names. Each property's value will
    be converted from a comma-separated string to a list.
    '''

    SPLIT_STR_SETS = ()
    '''
    Holds a tuple of configuration property names. Each property's value will
    be converted from a comma-separated string to a set.
    '''

    CAST_TO_BOOL = ()
    '''
    Holds a tuple of configuration property names. Each property's value will
    be cast from a string (you can find all possible values
    :ref:`here <allowed_values_booleans>`) to a boolean value.
    '''

    CAST_TO_INT = ()
    '''
    Holds a tuple of configuration property names. Each property's value will
    be cast from a string (which is number) to an integer.
    '''

    FILTER_SELECTORS = {}
    '''
    Holds a mapping of configuration property
    :ref:`selectors <configuration_selectors>` to a list of their entries. All
    entries of the selectors which are **not** in this list
    or **not** a valid entry will be ignored. Invalid entries will always be
    filtered.

    .. note::
      Each entry which is not filtered will automatically receive an ``id``
      property if one is not already set. The default value will be the name of
      the entry.
    '''

    VERIFY_VALUES = {}
    '''
    Holds a mapping of configuration property names to functions. The values of
    the property names will be given as an input to the supplied functions, and
    the results of these functions will **replace** the original values. The
    messages of any exceptions that occur during the execution of the functions
    will be aggregated and displayed as the message of a raised
    VerificationError exception.
    '''

    INCLUDE_PROPERTIES = ()
    '''
    Holds a tuple of configuration property names. Any property name that is
    **not** inside this tuple will be omitted from the end result
    '''

    @classmethod
    def read_and_parse_directory_configurations(
            cls, configurations_dir, defaults=None, fail_silently=False):
        '''
        Read and parse multiple configurations stored in a directory. This
        method will search recursively in the directory for configurations.

        :param str configuration_dir: directory which contains configurations.
        :param defaults: default values which will be used when configuration
                         file is readed.
        :param bool fail_silently: flag which will indicate if it will be
                                   raised :exc:`RuntimeError` exception if
                                   combination of configuration_dir and
                                   :attr:`ENABLED_DIR` doesn't exists.
        :type defaults: dict or None
        :return: list of read and parsed configurations.
        :rtype: list(Box)
        :raises RuntimeError: if fail_silently is False and combination of
                              configuration_dir and :attr:`ENABLED_DIR` doesn't
                              exists.
        '''
        if defaults is None:
            defaults = {}

        configs = cls.read_directory_configurations(
            configurations_dir, defaults=defaults, fail_silently=fail_silently
        )

        parsed_configs = []

        for config in configs:
            parsed_config = cls.parse(config)
            parsed_configs.append(parsed_config)

        return parsed_configs

    @classmethod
    def read_and_parse_file_configuration(
            cls, config_file, work_dir, defaults=None):
        '''
        Read and parse configuration stored in a file.

        :param str config_file: file which contains configuration.
        :param str work_dir: working directory which will be added as
                             ``work_dir`` and ``wd`` default values in the
                             configuration.
        :param defaults: default values which will be used when configuration
                         file is readed.
        :type defaults: dict or None
        :return: read and parsed configuration.
        :rtype: Box or None
        '''
        if defaults is None:
            defaults = {}

        config = cls.read_file_configuration(
            config_file, work_dir, defaults=defaults
        )

        config = cls.parse(config)

        return config

    @classmethod
    def read_directory_configurations(
            cls, configurations_dir, defaults=None, fail_silently=False):
        '''
        Read multiple configurations stored in a directory. This method will
        search recursively in the directory for configurations.

        :param str configuration_dir: directory which contains configurations.
        :param defaults: default values which will be used when configuration
                         file is readed.
        :param bool fail_silently: flag which will indicate if it will be
                                   raised :exc:`RuntimeError` exception if
                                   combination of configuration_dir and
                                   :attr:`ENABLED_DIR` doesn't exists.
        :type defaults: dict or None
        :return: list of read configurations.
        :rtype: list(Box)
        :raises RuntimeError: if fail_silently is False and combination of
                              configuration_dir and :attr:`ENABLED_DIR` doesn't
                              exists.
        '''
        if defaults is None:
            defaults = {}

        assert isinstance(configurations_dir, str), type(configurations_dir)

        enabled_dir = os.path.join(configurations_dir, cls.ENABLED_DIR)
        enabled_dir = os.path.abspath(enabled_dir)

        configs = []
        config_paths = cls._collect_config_paths(enabled_dir, fail_silently)

        for config_path in config_paths:
            config = cls.read_file_configuration(
                config_path, os.path.dirname(config_path), defaults
            )

            if config:
                configs.append(config)

        return configs

    @classmethod
    def read_file_configuration(cls, config_file, work_dir, defaults=None):
        '''
        Read configuration stored in a file.

        :param str config_file: file which contains configuration.
        :param str work_dir: working directory which will be added as
                             ``work_dir`` and ``wd`` default values in the
                             configuration.
        :param defaults: default values which will be used when configuration
                         file is readed.
        :type defaults: dict or None
        :return: read configuration.
        :rtype: Box or None
        '''
        if defaults is None:
            defaults = {}

        config = cls.read_config(config_file, work_dir, defaults)

        if config is None:
            return None

        config = Box(
            config, camel_killer_box=True, default_box=True,
            default_box_attr=None
        )

        config.config_file = config_file

        return config

    @classmethod
    def read_config(cls, config_file, work_dir, defaults=None):
        '''
        Read configuration stored in a file. Delimiter used in this
        configuration file must be ``=``. If :attr:`SECTION` is defined in the
        read configuration file then it would be checked if the configuration
        file is enabled.

        :param str config_file: file which contains configuration.
        :param str work_dir: working directory which will be added as
                             ``work_dir`` and ``wd`` default values in the
                             configuration.
        :param defaults: default values which will be used when configuration
                         file is readed. If this parameter is dict then it can
                         define the following properties:

                           * values - this property define dict which would be
                             added as default values for all of the
                             configurational sections.

                           * sections - with this property you can define dict
                             containing default values for particular section
                             in the configuration.

                           * override - with this property you can define dict
                             containing values which will be used for
                             overriding values in the particular section in the
                             configuration.

                           * conf - with this property you can define
                             configuration file. Values in the sections of this
                             configuration are used as default values to the
                             corresponding section in the read configuration.

        :type defaults: dict or None
        :return: read configuration.
        :rtype: dict or None
        '''
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
            strict=True,
            delimiters=('=')
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

        config = parser_to_dict(config_parser)

        if cls.SECTION in config:
            if 'enabled' in config[cls.SECTION]:
                if cls._str_to_bool(config[cls.SECTION]['enabled']) is False:
                    return None

        return config

    @classmethod
    def parse(cls, config):
        '''
        Parse :attr:`SECTION` section from configuration if it is defined else
        parse all of the sections in the configuration.

        :param config: configuration.
        :type config: Box or dict
        :return: parsed configuration.
        :rtype: Box or dict or None
        '''
        if not config:
            return None

        sections = list(config.keys())
        if cls.SECTION:
            sections = [cls.SECTION]

        for section in sections:
            config_section = config[section]
            if config_section is None:
                continue

            config_section = cls.parse_section(config_section)
            if config_section is None:
                config.pop(section)
                continue

            config[section] = config_section

        return config

    @classmethod
    def parse_section(cls, config_section):
        '''
        Parse one section from configuration based on the
        :attr:`SPLIT_STR_LISTS`, :attr:`SPLIT_STR_SETS`, :attr:`CAST_TO_BOOL`,
        :attr:`CAST_TO_INT`, :attr:`FILTER_SELECTORS` and :attr:`VERIFY_VALUES`
        class properties. If ``enabled`` property is defined in the
        configuration section then it would be checked if the configuration
        section is enabled.

        :param config_section: section from configuration.
        :type config_section: Box or dict
        :return: parsed configuration section.
        :rtype: Box or dict or None
        '''
        if config_section is None:
            return None
        if not isinstance(config_section, dict):
            return config_section
        if 'enabled' in config_section:
            if cls._str_to_bool(config_section['enabled']) is False:
                return None

        config_section = cls._split_str_lists(config_section)
        config_section = cls._split_str_sets(config_section)
        config_section = cls._cast_to_bool(config_section)
        config_section = cls._cast_to_int(config_section)
        config_section = cls._filter_selectors(config_section)
        config_section = cls._filter_included(config_section)

        # This one should remain last so as to avoid having a seemingly valid
        # value be rendered invalid by one of the previous transformations
        config_section = cls._verify_values(config_section)

        return config_section

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

    @staticmethod
    def _str_to_bool(val):
        true_values = ['yes', 'Yes', 'True', 'true']
        return True if val in true_values else False

    @staticmethod
    def _split_str_option_list(str_option, separator=','):
        if str_option is not None and str_option != '':
            return [el.strip() for el in str_option.split(separator)]
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
    def _filter_selectors(cls, config):
        for key, selected in cls.FILTER_SELECTORS.items():
            if key not in config:
                continue

            selected_elements = \
                config.get(selected, None) if selected else None

            def filter_selector(selector_key):
                if not isinstance(config[key][selector_key], dict):
                    return True

                if selected_elements and selector_key not in selected_elements:
                    return True

                return False

            keys_to_delete = tuple(filter(filter_selector, config[key]))

            for delele_key in keys_to_delete:
                config[key].pop(delele_key)

            for selector_id in config[key].keys():
                selector = config[key][selector_id]

                if not selector.id:
                    selector.id = selector_id

                config[key][selector_id] = selector

        return config

    @classmethod
    def _is_property_valid(cls, depth_stack, props):
        n_depth = 0
        n_prop = 0
        while n_depth <= len(depth_stack) and n_prop < len(props):
            if n_depth == len(depth_stack):
                if n_prop == len(props)-1:
                    return True
                else:
                    break
            prop_token = props[n_prop]

            depth_token = depth_stack[n_depth]
            if prop_token == '**':
                if n_prop == len(props) - 2:
                    return True
                else:
                    next_prop = prop_token[n_prop+1]
                    while n_depth < len(depth_stack):
                        depth_token = depth_stack[n_depth]
                        if depth_token == next_prop or next_prop == '*':
                            break
                        n_depth += 1
                    n_prop += 1
            elif prop_token != depth_token and prop_token != '*':
                return False
            n_depth += 1
            n_prop += 1
        return False

    @classmethod
    def _evaluate_included_properties(cls, depth_stack):
        split_props = list(map(lambda x: x.split('.'), cls.INCLUDE_PROPERTIES))
        valid_props = list()
        for prop_tokens in split_props:
            if cls._is_property_valid(depth_stack, prop_tokens):
                valid_props.append(prop_tokens[len(prop_tokens) - 1])
        return valid_props

    @classmethod
    def _filter_included(cls, config, depth_stack=deque()):
        if not cls.INCLUDE_PROPERTIES:
            return config

        evaluated_properties = cls._evaluate_included_properties(depth_stack)
        for k in list(config):
            if type(config[k]) == Box:
                depth_stack.append(k)
                cls._filter_included(config[k], depth_stack)
                depth_stack.pop()
                if len(config[k]) == 0:
                    del config[k]
            else:
                if k not in evaluated_properties \
                        and '*' not in evaluated_properties:
                    del config[k]

        return config

    @classmethod
    def _verify_values(cls, config):
        exception_messages = []

        for key, verify_func in cls.VERIFY_VALUES.items():
            if key in config:
                try:
                    config[key] = verify_func(config[key])
                except Exception as e:
                    exception_messages.append('[{}]: {}'.format(key, str(e)))

        if exception_messages:
            raise VerificationError('\n'.join(exception_messages))

        return config
