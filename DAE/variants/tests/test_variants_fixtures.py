'''
Created on Jun 15, 2018

@author: lubo
'''
import pytest
from RegionOperations import Region
from datasets.helpers import mat2str


@pytest.mark.parametrize("fixture_name", [
    # "fixtures/effects_trio_multi",
    # "fixtures/effects_trio",
    # "fixtures/inheritance_multi",
    "fixtures/trios2",
])
@pytest.mark.parametrize("variants", [
    "variants_df",
    "variants_vcf",
])
def test_df_query_multiallelic3_families(
        variants_impl, variants, fixture_name):

    dfvars = variants_impl(variants)(fixture_name)
    assert dfvars is not None

    regions = [Region('1', 11606, 11606)]
    family_ids = ['f1']
    vs = dfvars.query_variants(regions=regions, family_ids=family_ids)
    vs = list(vs)
    assert len(vs) == 1
    print(vs)
    v = vs[0]

    print(mat2str(v.best_st))

    assert mat2str(v.best_st) == "1 1 2/1 0 0/0 1 0"
    assert "mom1" in v.variant_in_members
    assert "dad1" in v.variant_in_members
    assert "ch1" not in v.variant_in_members
