import pytest


@pytest.mark.parametrize("fixture_name", [
    "fixtures/a",
])
def test_variants_serialize(impala_parquet_variants, fixture_name):
    impala_parquet_variants(fixture_name)

