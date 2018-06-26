'''
Created on Jun 7, 2018

@author: lubo
'''


import pytest
from RegionOperations import Region
from variants.vcf_utils import mat2str


@pytest.mark.parametrize("fixture_name,count", [
    # "fixtures/effects_trio_multi",
    ("fixtures/effects_trio", 10),
    ("fixtures/inheritance_multi", 6),
    # ("fixtures/trios2", 30),
])
def test_df_all_variants(variants_df, fixture_name, count):

    dfvars = variants_df(fixture_name)
    assert dfvars is not None

    vs = dfvars.query_variants()
    vs = list(vs)
    assert len(vs) == count


@pytest.mark.parametrize("fixture_name", [
    # "fixtures/effects_trio_multi",
    # "fixtures/effects_trio",
    # "fixtures/inheritance_multi",
    "fixtures/trios2",
])
def test_df_query_regions(variants_df, fixture_name):

    dfvars = variants_df(fixture_name)
    assert dfvars is not None

    regions = [Region('1', 11539, 11539)]
    vs = dfvars.query_variants(regions=regions)
    assert len(list(vs)) == 2

    regions = [Region('1', 11539, 11539), Region('1', 11540, 11540)]
    vs = dfvars.query_variants(regions=regions)
    assert len(list(vs)) == 4


@pytest.mark.parametrize("fixture_name", [
    # "fixtures/effects_trio_multi",
    # "fixtures/effects_trio",
    # "fixtures/inheritance_multi",
    "fixtures/trios2",
])
def test_df_query_families(variants_df, fixture_name):

    dfvars = variants_df(fixture_name)
    assert dfvars is not None

    regions = [Region('1', 11539, 11539)]
    family_ids = ['f1']
    vs = dfvars.query_variants(regions=regions, family_ids=family_ids)
    vs = list(vs)
    assert len(vs) == 1
    print(vs)


@pytest.mark.parametrize("fixture_name", [
    # "fixtures/effects_trio_multi",
    # "fixtures/effects_trio",
    # "fixtures/inheritance_multi",
    "fixtures/trios2",
])
def test_df_query_multiallelic_families(variants_df, fixture_name):

    dfvars = variants_df(fixture_name)
    assert dfvars is not None

    regions = [Region('1', 11605, 11605)]
    family_ids = ['f1']
    vs = dfvars.query_variants(regions=regions, family_ids=family_ids)
    vs = list(vs)
    assert len(vs) == 1
    print(vs)
    v = vs[0]

    print(mat2str(v.best_st))

    assert "mom1" in v.variant_in_members
    assert "dad1" in v.variant_in_members
    assert "ch1" not in v.variant_in_members


@pytest.mark.parametrize("fixture_name", [
    # "fixtures/effects_trio_multi",
    # "fixtures/effects_trio",
    # "fixtures/inheritance_multi",
    "fixtures/trios2",
])
def test_df_query_multiallelic3_families(variants_df, fixture_name):

    dfvars = variants_df(fixture_name)
    assert dfvars is not None

    regions = [Region('1', 11606, 11606)]
    family_ids = ['f1']
    vs = dfvars.query_variants(regions=regions, family_ids=family_ids)
    vs = list(vs)
    assert len(vs) == 1
    print(vs)
    v = vs[0]

    print(mat2str(v.best_st))

    assert "mom1" in v.variant_in_members
    assert "dad1" in v.variant_in_members
    assert "ch1" not in v.variant_in_members
