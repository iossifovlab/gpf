import pytest
from dae.annotation.tools.file_io import parquet_enabled
from dae.annotation.tools.schema import Schema

if parquet_enabled:
    import pyarrow as pa
    from dae.annotation.tools.file_io_parquet import ParquetSchema


@pytest.fixture
def sample_schema_dict():
    return {"str": ["chr", "position", "variant"], "float": ["dummy_score"]}


@pytest.fixture
def generic_schema():
    return Schema.from_dict(
        {"str": ["col1", "col2", "col3"], "float": ["col4", "col5", "col6"]}
    )


@pytest.mark.skipif(
    parquet_enabled is False, reason="pyarrow module not installed"
)
@pytest.fixture
def generic_pq_schema():
    return ParquetSchema.from_dict(
        {"str": ["col1", "col2", "col3"], "float": ["col4", "col5", "col6"]}
    )


@pytest.fixture
def generic_schema_alt():
    return Schema.from_dict(
        {"str": ["col1", "col7", "col8"], "float": ["col11", "col12", "col6"]}
    )


@pytest.mark.skipif(
    parquet_enabled is False, reason="pyarrow module not installed"
)
@pytest.fixture
def generic_pa_schema():
    return pa.schema(
        [
            pa.field("col1", pa.string()),
            pa.field("col2", pa.string()),
            pa.field("col3", pa.string()),
            pa.field("col4", pa.float64()),
            pa.field("col5", pa.float64()),
            pa.field("col6", pa.float64()),
        ]
    )


def test_schema_from_config(sample_schema_dict):
    expected_columns = {
        "chr": "str",
        "position": "str",
        "variant": "str",
        "dummy_score": "float",
    }
    schema = Schema.from_dict(sample_schema_dict)

    for col, type_ in expected_columns.items():
        assert col in schema.columns
        assert type_ == schema.columns[col].type_name


def test_merge_schemas(generic_schema, generic_schema_alt):
    schema = Schema.merge_schemas(generic_schema, generic_schema_alt)
    expected_cols = [
        "col1",
        "col2",
        "col3",
        "col4",
        "col5",
        "col6",
        "col7",
        "col8",
        "col11",
        "col12",
    ]
    assert list(schema.columns.keys()) == expected_cols


# FIXME:
@pytest.mark.xfail(reason="recieved DataType(double) instead of (float)")
@pytest.mark.skipif(
    parquet_enabled is False, reason="pyarrow module not installed"
)
def test_to_arrow(generic_pq_schema, generic_pa_schema):
    converted_schema = generic_pq_schema.to_arrow()
    assert [name in generic_pa_schema.names for name in converted_schema.names]
    for name in converted_schema.names:
        assert (
            converted_schema.field(name).type
            == generic_pa_schema.field(name).type
        )


# FIXME:
@pytest.mark.xfail(reason="recieved DataType(double) instead of (float)")
@pytest.mark.skipif(
    parquet_enabled is False, reason="pyarrow module not installed"
)
def test_from_arrow(generic_pq_schema, generic_pa_schema):
    converted_schema = ParquetSchema.from_arrow(generic_pa_schema)
    assert [
        col in generic_pq_schema.columns for col in converted_schema.columns
    ]
    for col in converted_schema.columns:
        assert (
            converted_schema.columns[col].type_name
            == generic_pq_schema.columns[col].type_name
        )
        assert (
            converted_schema.columns[col].type_py
            == generic_pq_schema.columns[col].type_py
        )
        assert (
            converted_schema.columns[col].type_pa
            == generic_pq_schema.columns[col].type_pa
        )


def test_order_as(generic_schema):
    new_col_order = ["col5", "col2", "col3", "col4", "col1", "col6"]
    ordered_schema = generic_schema.order_as(new_col_order)
    assert ordered_schema.col_names == new_col_order
