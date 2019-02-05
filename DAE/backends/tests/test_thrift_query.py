from RegionOperations import Region
from ..thrift.thrift_query import ThriftQueryBuilder


def test_simple_summary_subquery(parquet_variants):
    parquet = parquet_variants("fixtures/effects_trio")
    print(parquet)

    query = {
        'genes': ['SAMD11', 'PLEKHN1'],
        'effect_types': ['missense', 'frame-shift'],
        'regions': [Region('1', 865582, 865691), Region('2', 20001, 20010)]
    }

    builder = ThriftQueryBuilder(
        query=query, summary_schema={}, tables=parquet)
    assert builder is not None
    print(builder.build())


def test_simple_summary_subquery_regions_only(parquet_variants):
    parquet = parquet_variants("fixtures/effects_trio")
    print(parquet)

    query = {
        'regions': [Region('1', 865582, 865691), Region('2', 20001, 20010)]
    }

    builder = ThriftQueryBuilder(
        query=query, summary_schema={}, tables=parquet)
    assert builder is not None
    print(builder.build())
