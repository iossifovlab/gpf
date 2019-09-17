import pytest

from box import Box

from dae.configuration.tests.conftest import relative_to_this_test_folder

from dae.configuration.config_parser_base import ConfigParserBase, \
    VerificationError


class ConfigParserTestWrapper(ConfigParserBase):

    ENABLED_DIR = 'configs'

    SPLIT_STR_LISTS = (
        'list',
        'missing',
    )
    SPLIT_STR_SETS = (
        'set',
        'missing',
    )
    CAST_TO_BOOL = (
        'bool',
        'missing',
    )
    CAST_TO_INT = (
        'int',
        'missing',
    )
    FILTER_SELECTORS = {
        'selector': 'selected',
        'selector_no_selected': None,
        'missing': None
    }
    VERIFY_VALUES = {
        'to_verify1': len,
        'to_verify2': len,
        'to_verify3': len,
    }


class SectionConfigParserTestWrapper(ConfigParserTestWrapper):

    SECTION = 'section'


def test_read_and_parse_directory_configurations():
    configs = ConfigParserTestWrapper.read_and_parse_directory_configurations(
        relative_to_this_test_folder('fixtures'),
        defaults={'sections': {'dir': {'int': '7'}}}
    )

    assert len(configs) == 3

    assert sorted([config.config_file for config in configs]) == sorted([
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        relative_to_this_test_folder('fixtures/configs/test.conf'),
        relative_to_this_test_folder('fixtures/configs/sub_configs/sub.conf')
    ])

    assert sorted([config.dir.wd for config in configs]) == sorted([
        relative_to_this_test_folder('fixtures/configs'),
        relative_to_this_test_folder('fixtures/configs'),
        relative_to_this_test_folder('fixtures/configs')
    ])

    assert configs[0].dir.int == 7
    assert configs[1].dir.int == 7
    assert configs[2].dir.int == 7


def test_read_and_parse_directory_configurations_empty_path():
    with pytest.raises(RuntimeError) as err:
        ConfigParserBase.read_and_parse_directory_configurations(
            relative_to_this_test_folder('ala bala')
        )

    assert str(err.value) == relative_to_this_test_folder('ala bala')


def test_read_and_parse_directory_configurations_empty_path_fail_silently():
    config_paths = ConfigParserBase.read_and_parse_directory_configurations(
        'ala bala', fail_silently=True
    )

    assert config_paths == []


def test_read_and_parse_file_configuration():
    config = ConfigParserTestWrapper.read_and_parse_file_configuration(
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        'ala_bala', {
            'values': {'int': '7'},
            'sections': {'section': {'key': 'value'}},
            'override': {'configuration': {'selected': 'a'}},
            'conf': relative_to_this_test_folder(
                'fixtures/configs/sub_configs/sub.conf'
            )
        }
    )

    assert isinstance(config, Box)

    assert config.config_file == \
        relative_to_this_test_folder('fixtures/configs/config.conf')

    assert config.section is None

    assert config.configuration.int == 7
    assert config.configuration.bool is True
    assert config.configuration.set == {'c', 'd'}
    assert config.configuration.dir == 'ala_bala_portokala'
    assert config.configuration.list == ['a', 'b']
    assert config.configuration.selected == 'a'

    assert config.configuration.selector.a.key == 'value'

    assert config.configuration.selector_no_selected.a.key == 'value'
    assert config.configuration.selector_no_selected.b.value == 'key'
    assert config.configuration.selector_no_selected.c is None

    assert config is not None


def test_read_and_parse_file_configuration_disabled():
    config = SectionConfigParserTestWrapper.read_and_parse_file_configuration(
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        'ala_bala'
    )

    assert config is None


def test_read_directory_configurations():
    configs = ConfigParserTestWrapper.read_directory_configurations(
        relative_to_this_test_folder('fixtures'),
        defaults={'sections': {'dir': {'int': '7'}}}
    )

    assert len(configs) == 3

    assert sorted([config.config_file for config in configs]) == sorted([
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        relative_to_this_test_folder('fixtures/configs/test.conf'),
        relative_to_this_test_folder('fixtures/configs/sub_configs/sub.conf')
    ])

    assert sorted([config.dir.wd for config in configs]) == sorted([
        relative_to_this_test_folder('fixtures/configs'),
        relative_to_this_test_folder('fixtures/configs'),
        relative_to_this_test_folder('fixtures/configs')
    ])

    assert configs[0].dir.int == '7'
    assert configs[1].dir.int == '7'
    assert configs[2].dir.int == '7'


def test_read_directory_configurations_empty_path():
    with pytest.raises(RuntimeError) as err:
        ConfigParserBase.read_directory_configurations(
            relative_to_this_test_folder('ala bala')
        )

    assert str(err.value) == relative_to_this_test_folder('ala bala')


def test_read_directory_configurations_empty_path_fail_silently():
    config_paths = ConfigParserBase.read_directory_configurations(
        'ala bala', fail_silently=True
    )

    assert config_paths == []


def test_read_file_configuration():
    config = ConfigParserTestWrapper.read_file_configuration(
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        'ala_bala', {
            'values': {'int': '7'},
            'sections': {'section': {'key': 'value'}},
            'override': {'configuration': {'selected': 'a'}},
            'conf': relative_to_this_test_folder(
                'fixtures/configs/sub_configs/sub.conf'
            )
        }
    )

    assert isinstance(config, Box)

    assert config._box_config['camel_killer_box'] is True
    assert config._box_config['default_box'] is True
    assert config._box_config['default_box_attr'] is None

    assert config.config_file == \
        relative_to_this_test_folder('fixtures/configs/config.conf')

    assert config.section.int == '7'
    assert config.section.bool == 'Yes'
    assert config.section.set == 'c, d'
    assert config.section.dir == 'ala_bala_portokala'
    assert config.section.enabled == 'no'
    assert config.section.key == 'value'

    assert config.configuration.int == '7'
    assert config.configuration.bool == 'Yes'
    assert config.configuration.set == 'c, d'
    assert config.configuration.dir == 'ala_bala_portokala'
    assert config.configuration.list == 'a,b'
    assert config.configuration.selected == 'a'

    assert config.configuration.selector.a.key == 'value'
    assert config.configuration.selector.b.value == 'key'
    assert config.configuration.selector.c == 'ala bala'

    assert config.configuration.selector_no_selected.a.key == 'value'
    assert config.configuration.selector_no_selected.b.value == 'key'
    assert config.configuration.selector_no_selected.c == 'ala bala'

    assert config is not None


def test_read_file_configuration_disabled():
    config = SectionConfigParserTestWrapper.read_file_configuration(
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        'ala_bala'
    )

    assert config is None


def test_collect_config_paths():
    config_paths = ConfigParserBase._collect_config_paths(
        relative_to_this_test_folder('fixtures/configs'))

    assert len(config_paths) == 3

    assert sorted(config_paths) == sorted([
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        relative_to_this_test_folder('fixtures/configs/test.conf'),
        relative_to_this_test_folder('fixtures/configs/sub_configs/sub.conf')
    ])


def test_collect_cosnfig_paths_missing_path():
    with pytest.raises(RuntimeError) as err:
        ConfigParserBase._collect_config_paths('ala bala')

    assert str(err.value) == 'ala bala'


def test_collect_cosnfig_paths_missing_path_fail_silently():
    config_paths = \
        ConfigParserBase._collect_config_paths('ala bala', fail_silently=True)

    assert config_paths == []


def test_read_config():
    config = ConfigParserTestWrapper.read_config(
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        'ala_bala', {
            'values': {'int': '7'},
            'sections': {'section': {'key': 'value'}},
            'override': {'configuration': {'selected': 'a'}},
            'conf': relative_to_this_test_folder(
                'fixtures/configs/sub_configs/sub.conf'
            )
        }
    )

    assert isinstance(config, dict)

    assert config['section']['int'] == '7'
    assert config['section']['bool'] == 'Yes'
    assert config['section']['set'] == 'c, d'
    assert config['section']['dir'] == 'ala_bala_portokala'
    assert config['section']['enabled'] == 'no'
    assert config['section']['key'] == 'value'

    assert config['configuration']['int'] == '7'
    assert config['configuration']['bool'] == 'Yes'
    assert config['configuration']['set'] == 'c, d'
    assert config['configuration']['dir'] == 'ala_bala_portokala'
    assert config['configuration']['list'] == 'a,b'
    assert config['configuration']['selected'] == 'a'

    assert config['configuration']['selector']['a']['key'] == 'value'
    assert config['configuration']['selector']['b']['value'] == 'key'
    assert config['configuration']['selector']['c'] == 'ala bala'

    assert config['configuration']['selector_no_selected']['a']['key'] == \
        'value'
    assert config['configuration']['selector_no_selected']['b']['value'] == \
        'key'
    assert config['configuration']['selector_no_selected']['c'] == 'ala bala'

    assert config is not None


def test_read_config_disabled():
    config = SectionConfigParserTestWrapper.read_config(
        relative_to_this_test_folder('fixtures/configs/config.conf'),
        'ala_bala'
    )

    assert config is None


def test_parse_one_section():
    config = SectionConfigParserTestWrapper.parse(
        Box({
            'section': {'bool': 'no', 'list': 'a,b'},
            'no_parse': {'bool': 'no', 'list': 'a,b'},
            'disabled': {'enabled': 'No'}
        })
    )

    assert len(config) == 3

    assert config['section']['bool'] is False
    assert config['section']['list'] == ['a', 'b']

    assert config['no_parse']['bool'] == 'no'
    assert config['no_parse']['list'] == 'a,b'

    assert config['disabled']['enabled'] == 'No'


def test_parse_all_section():
    config = ConfigParserTestWrapper.parse(
        Box({
            'section': {'bool': 'no', 'list': 'a,b'},
            'parse': {'bool': 'Yes', 'set': 'a,b'},
            'disabled': {'enabled': 'No'}
        })
    )

    assert len(config) == 2

    assert config['section']['bool'] is False
    assert config['section']['list'] == ['a', 'b']

    assert config['parse']['bool'] is True
    assert config['parse']['set'] == {'a', 'b'}


def test_parse_disabled():
    assert ConfigParserBase.parse(None) is None
    assert ConfigParserBase.parse('') is None


def test_parse_section():
    config = ConfigParserTestWrapper.parse_section(Box({
        'list': 'a,b',
        'set': 'c,d',
        'bool': 'true',
        'int': '7',
        'selector': {
            'a': {'key': 'value'},
            'b': {'value': 'key'},
            'c': 'ala bala'
        },
        'selected': ['a'],
        'selector_no_selected': {
            'a': {'key': 'value'},
            'b': {'value': 'key'},
            'c': 'ala bala'
        },
    }, default_box=True, default_box_attr=None))

    assert len(config) == 7

    assert config['list'] == ['a', 'b']
    assert config['set'] == {'c', 'd'}
    assert config['bool'] is True
    assert config['int'] == 7
    assert config['selector']['a']['id'] == 'a'


def test_parse_section_disabled():
    assert ConfigParserBase.parse_section(None) is None
    assert ConfigParserBase.parse_section('None') == 'None'
    assert ConfigParserBase.parse_section('') == ''
    assert ConfigParserBase.parse_section({'enabled': 'no'}) is None
    assert ConfigParserBase.parse_section({'enabled': 'yes'}) == \
        {'enabled': 'yes'}


def test_str_to_bool():
    assert ConfigParserBase._str_to_bool('yes') is True
    assert ConfigParserBase._str_to_bool('Yes') is True
    assert ConfigParserBase._str_to_bool('True') is True
    assert ConfigParserBase._str_to_bool('true') is True

    assert ConfigParserBase._str_to_bool('no') is False
    assert ConfigParserBase._str_to_bool('No') is False
    assert ConfigParserBase._str_to_bool('False') is False
    assert ConfigParserBase._str_to_bool('false') is False

    assert ConfigParserBase._str_to_bool('ala bala') is False


def test_split_str_option_list():
    assert ConfigParserBase._split_str_option_list(
        'ala, bala  ,portokala  ') == ['ala', 'bala', 'portokala']
    assert ConfigParserBase._split_str_option_list(
        'ala: bala  :portokala  ', separator=':') == \
        ['ala', 'bala', 'portokala']

    assert ConfigParserBase._split_str_option_list('') == []
    assert ConfigParserBase._split_str_option_list(None) == []


def test_split_str_lists():
    config = ConfigParserTestWrapper._split_str_lists(
        Box({'list': 'a,b', 'set': 'c,d'})
    )

    assert len(config) == 2

    assert config['list'] == ['a', 'b']
    assert config['set'] == 'c,d'


def test_split_str_sets():
    config = ConfigParserTestWrapper._split_str_sets(
        Box({'list': 'a,b', 'set': 'c,d'})
    )

    assert len(config) == 2

    assert config['list'] == 'a,b'
    assert config['set'] == {'c', 'd'}


def test_cast_to_bool():
    config = ConfigParserTestWrapper._cast_to_bool(
        Box({'bool': 'no', 'list': 'a,b'})
    )

    assert len(config) == 2

    assert config['bool'] is False
    assert config['list'] == 'a,b'


def test_cast_to_int():
    config = ConfigParserTestWrapper._cast_to_int(
        Box({'int': '7', 'list': 'a,b'})
    )

    assert len(config) == 2

    assert config['int'] == 7
    assert config['list'] == 'a,b'


def test_filter_selectors():
    config = ConfigParserTestWrapper._filter_selectors(Box({
        'selector': {
            'a': {'key': 'value'},
            'b': {'value': 'key'},
            'c': 'ala bala'
        },
        'selected': ['a'],
        'selector_no_selected': {
            'a': {'key': 'value'},
            'b': {'value': 'key'},
            'c': 'ala bala'
        },
        'list': 'a,b'
    }, default_box=True, default_box_attr=None))

    assert len(config) == 4

    assert list(config['selector'].keys()) == ['a']
    assert config['selector']['a']['id'] == 'a'
    assert config['selected'] == ['a']
    assert sorted(list(config['selector_no_selected'].keys())) == \
        sorted(['a', 'b'])
    assert config['selector_no_selected']['a']['id'] == 'a'
    assert config['selector_no_selected']['b']['id'] == 'b'

    assert config['list'] == 'a,b'


def test_verify_values():
    with pytest.raises(VerificationError) as excinfo:
        ConfigParserTestWrapper._verify_values(
            Box({'to_verify1': 1, 'to_verify2': 'a,b', 'to_verify3': True})
        )

    assert str(excinfo.value) == \
        ("[to_verify1]: object of type 'int' has no len()\n"
         "[to_verify3]: object of type 'bool' has no len()")


    config = ConfigParserTestWrapper._verify_values(
        Box({'to_verify1': [1], 'to_verify2': 'ab', 'to_verify3': [1, 2, 3]})
    )

    assert config.to_verify1 == 1
    assert config.to_verify2 == 2
    assert config.to_verify3 == 3
