import pytest
import pyarrow as pa
from annotation.tools.file_io import Schema


@pytest.fixture
def sample_schema_dict():
    return {'str': 'chr,position,variant',
            'float': 'dummy_score'}


@pytest.fixture
def generic_schema():
    return Schema.from_dict({'str': 'col1,col2,col3',
                             'float': 'col4,col5,col6'})


@pytest.fixture
def generic_schema_alt():
    return Schema.from_dict({'str': 'col1,col7,col8',
                             'float': 'col11,col12,col6'})


@pytest.fixture
def generic_pa_schema():
    return pa.schema([pa.field('col1', pa.string()),
                      pa.field('col2', pa.string()),
                      pa.field('col3', pa.string()),
                      pa.field('col4', pa.float64()),
                      pa.field('col5', pa.float64()),
                      pa.field('col6', pa.float64())])


def test_schema_from_config(sample_schema_dict):
    expected_columns = {'chr': 'str', 'position': 'str',
                        'variant': 'str', 'dummy_score': 'float'}
    schema = Schema.from_dict(sample_schema_dict)

    for col, type_ in expected_columns.items():
        assert col in schema.columns
        assert type_ == schema.columns[col].type_name


def test_merge_schemas(generic_schema, generic_schema_alt):
    schema = Schema.merge_schemas(generic_schema, generic_schema_alt)
    expected_cols = ['col1', 'col2', 'col3', 'col4', 'col5',
                     'col6', 'col7', 'col8', 'col11', 'col12']
    assert list(schema.columns.keys()) == expected_cols


def test_to_arrow(generic_schema, generic_pa_schema):
    assert generic_schema.to_arrow() == generic_pa_schema


def test_from_arrow(generic_schema, generic_pa_schema):
    schema_from_pa = Schema.from_arrow(generic_pa_schema)
    assert schema_from_pa.columns == generic_schema.columns
