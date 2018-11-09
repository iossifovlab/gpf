from __future__ import unicode_literals
import pytest


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # "variants_df",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,phenotype,count", [
    ("fixtures/effects_trio_dad", 'autism', 2),
    ("fixtures/effects_trio_dad", 'unaffected', 2),
    ("fixtures/effects_trio_dad", 'schizophrenia', 0)
])
def test_fixture_query_by_sex(
        variants_impl, variants, fixture_name, phenotype, count):
    vvars = variants_impl(variants)(fixture_name)
    # vvars = variants_df(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        pedigreeSelector={'checkedValues': [phenotype], 'source': 'phenotype'})
    vs = list(vs)
    assert len(vs) == count
