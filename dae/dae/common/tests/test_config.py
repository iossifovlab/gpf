import pytest

import dae.common.config

from dae.configuration.dae_config_parser import CaseSensitiveConfigParser


def test_config_to_dict(configuration):
    result = dae.common.config.to_dict(configuration)
    assert result is not None

    sections = list(result.keys())

    assert sections[0] == 'Step1'
    assert len(sections) == 5

    assert sections == ['Step1', 'Step2', 'Step3', 'Step4', 'Step5', ]


def test_config_to_dict_selectors():
    config_parser = CaseSensitiveConfigParser()
    selector_dict = {
        'Section1': {
            'Property': 'value',
            'Selector1.property1.key1': 'value1',
            'Selector1.property1.key2': 'value2',
            'Selector1.property2.key2': 'value4',
            'Selector1.property3.key1': 'value5',
            'Selector1.property3.key2': 'value6',
            'property4.key3': 'value1',
            'property4.key4': 'value2',
            'property5.key3': 'value3',
            'property5.key4': 'value4',
        }, 'Section2': {
            'Property1': 'value1',
            'Property2': 'value2'
        }
    }

    config_parser.read_dict(selector_dict)
    result = dae.common.config.to_dict(config_parser)
    assert result is not None

    assert len(list(result.keys())) == 2
    assert list(result.keys()) == ['Section1', 'Section2']

    assert len(list(result['Section1'].keys())) == 4
    assert list(result['Section1'].keys()) == [
        'Property', 'Selector1', 'property4', 'property5'
    ]

    assert result['Section1']['Property'] == 'value'

    assert len(list(result['Section1']['Selector1'].keys())) == 3
    assert list(result['Section1']['Selector1'].keys()) == [
        'property1', 'property2', 'property3'
    ]

    assert result['Section1']['Selector1']['property1'] == {
        'key1': 'value1',
        'key2': 'value2'
    }
    assert result['Section1']['Selector1']['property2'] == {
        'key2': 'value4'
    }
    assert result['Section1']['Selector1']['property3'] == {
        'key1': 'value5',
        'key2': 'value6'
    }

    assert result['Section1']['property4'] == {
        'key3': 'value1',
        'key4': 'value2'
    }
    assert result['Section1']['property5'] == {
        'key3': 'value3',
        'key4': 'value4'
    }

    assert result['Section2'] == {
        'Property1': 'value1',
        'Property2': 'value2'
    }


@pytest.mark.skip()
def test_config_to_dict_section_selectors():
    config_parser = CaseSensitiveConfigParser()
    selector_dict = {
        'Section1.First': {
            'Property': 'value',
            'Selector1.property1.key1': 'value1',
            'Selector1.property1.key2': 'value2',
            'Selector1.property2.key2': 'value3',
            'property3.key3': 'value4',
            'property3.key4': 'value5',
        }, 'Section1.Second': {
            'Property1': 'value1',
        }, 'Section2': {
            'Property1': 'value1',
            'Property2': 'value2'
        }
    }

    config_parser.read_dict(selector_dict)
    result = dae.common.config.to_dict(config_parser)
    assert result is not None

    assert len(list(result.keys())) == 2
    assert list(result.keys()) == ['Section1', 'Section2']

    assert len(list(result['Section1'].keys())) == 2
    assert list(result['Section1'].keys()) == ['First', 'Second']

    assert len(list(result['Section1']['First'].keys())) == 4
    assert list(result['Section1']['First'].keys()) == [
        'Property', 'Selector1', 'property3'
    ]

    assert result['Section1']['First']['Property'] == 'value'

    assert len(list(result['Section1']['First']['Selector1'].keys())) == 2
    assert list(result['Section1']['First']['Selector1'].keys()) == [
        'property1', 'property2'
    ]

    assert result['Section1']['First']['Selector1']['property1'] == {
        'key1': 'value1',
        'key2': 'value2'
    }
    assert result['Section1']['First']['Selector1']['property2'] == {
        'key2': 'value3'
    }

    assert result['Section1']['First']['property3'] == {
        'key3': 'value4',
        'key4': 'value5'
    }

    assert len(list(result['Section1']['Second'].keys())) == 1
    assert list(result['Section1']['Second'].keys()) == ['Property1']

    assert result['Section1']['Second']['Property1'] == 'value1'

    assert result['Section2'] == {
        'Property1': 'value1',
        'Property2': 'value2'
    }
