import pytest
import pyarrow as pa
from annotation.tools.file_io import Schema
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


@pytest.fixture
def generic_schema():
    return Schema({'str': 'col1,col2,col3',
                   'float': 'col4,col5,col6'})


@pytest.fixture
def generic_schema_alt():
    return Schema({'str': 'col1,col7,col8',
                   'float': 'col11,col12,col6'})


@pytest.fixture
def generic_pa_schema():
    return pa.schema([pa.field('col1', pa.string()),
                      pa.field('col2', pa.string()),
                      pa.field('col3', pa.string()),
                      pa.field('col4', pa.float64()),
                      pa.field('col5', pa.float64()),
                      pa.field('col6', pa.float64())])


def test_schema_from_config(sample_config):
    expected_columns = {'chr': 'str', 'position': 'str',
                        'variant': 'str', 'dummy_score': 'float'}
    conf_parser = ConfigParser()
    conf_parser.read_file(sample_config)
    conf_schema = Schema(dict(conf_parser.items('schema')))

    for col, type_ in expected_columns.items():
        assert col in conf_schema.column_map
        assert type_ == conf_schema.column_map[col]


def test_merge_schemas(generic_schema, generic_schema_alt):
    generic_schema.merge(generic_schema_alt)
    expected_cols = ['col1', 'col2', 'col3', 'col4', 'col5',
                     'col6', 'col7', 'col8', 'col11', 'col12']
    assert list(generic_schema.column_map.keys()) == expected_cols


def test_rename_column(generic_schema):
    generic_schema.rename_column('col1', 'newColName')
    assert 'newColName' in generic_schema.column_map


def test_isolate_columns(generic_schema):
    generic_schema.isolate_columns(['col3', 'col5'])
    assert list(generic_schema.column_map.keys()) == ['col3', 'col5']


def test_to_arrow(generic_schema, generic_pa_schema):
    assert generic_schema.to_arrow() == generic_pa_schema


def test_from_arrow(generic_schema, generic_pa_schema):
    schema_from_pa = Schema()
    schema_from_pa.from_arrow(generic_pa_schema)
    assert schema_from_pa.column_map == generic_schema.column_map


def test_column_coercion(generic_schema):
    def recursive_coerce(data):
        if type(data) is list:
            return [recursive_coerce(elem) for elem in data]
        else:
            return float(data)

    col1 = [1, 2.5, 3, 'a', -5, 6, 'b']
    col4 = [[1.5, 4.3], ['-3.4', '6.4'], [5.0, '4.2']]
    assert generic_schema.coerce_column('col1', col1) \
        == list(map(str, col1))
    assert generic_schema.coerce_column('col4', col4) \
        == list(map(recursive_coerce, col4))
