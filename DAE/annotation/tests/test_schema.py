import pytest
from annotation.tools.file_io import Schema
from annotation.tools.annotate_score_base import conf_to_dict
from configparser import ConfigParser
from io import StringIO

@pytest.fixture
def sample_config():
    conf = (
        '[general]\n'
        'header=chr,position,variant,dummy_score\n'
        'noScoreValue=-100\n'
        '[columns]\n'
        'chr=chr\n'
        'pos_begin=position\n'
        'score=dummy_score\n'
        '[schema]\n'
        'str=chr,position,variant\n'
        'float=dummy_score\n'
        )
    return StringIO(conf)

def test_schema_from_config(sample_config):
    expected_columns = {'chr': 'str', 'position': 'str',
                  'variant': 'str', 'dummy_score': 'float'}
    parsed_conf = conf_to_dict(sample_config)

    for col, type_ in expected_columns.items():
        assert(col in parsed_conf['schema'].column_map)
        assert(type_ == parsed_conf['schema'].column_map[col])


def test_merge_schemas():
    schema_1 = Schema([('str', 'col1,col2,col3'),
                       ('float', 'col4,col5,col6',)])
    schema_2 = Schema([('str', 'col1,col7,col8'),
                       ('float', 'col11,col12,col6')])
    expected_schema = Schema([('str','col1,col2,col3,col7,col8'),
                              ('float','col4,col5,col6,col11,col12')])

    schema_1.merge(schema_2)
    assert(schema_1.column_map == expected_schema.column_map)


def test_merge_columns():
    schema = Schema([('str', 'col1,col2,col3'),
                     ('float', 'col4,col5,col6',)])
    expected_schema = Schema([('str', 'merged_str_col'),
                              ('float', 'merged_float_col',)])

    schema.merge_columns(['col1','col2', 'col3'], 'merged_str_col')
    schema.merge_columns(['col4','col5', 'col6'], 'merged_float_col')
    assert(schema.column_map == expected_schema.column_map)


def test_query_by_type():
    schema = Schema([('str', 'col1,col2,col3'),
                       ('float', 'col4,col5,col6',)])
    expected_str_cols = ['col1','col2', 'col3']
    expected_float_cols = ['col4','col5', 'col6']
    assert(schema.type_query('str') == expected_str_cols)
    assert(schema.type_query('float') == expected_float_cols)
