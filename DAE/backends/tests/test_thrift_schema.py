import pytest


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio",
    # "fixtures/inheritance_multi",
])
def test_variants_thrift_summary_schema(variants_thrift, fixture_name):

    svars = variants_thrift(fixture_name)
    assert svars is not None
    assert svars.summary_schema is not None

    print(svars.summary_schema)

    assert 'af_parents_called_percent' in svars.summary_schema
    assert svars.summary_schema['af_parents_called_percent'] == 'double'

    assert 'af_allele_freq' in svars.summary_schema
    assert svars.summary_schema['af_allele_freq'] == 'double'
