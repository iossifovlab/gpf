'''
Created on Jun 7, 2018

@author: lubo
'''


import pytest
import numpy as np
from RegionOperations import Region


@pytest.mark.parametrize("fixture_name", [
    # "fixtures/effects_trio_multi",
    # "fixtures/effects_trio",
    # "fixtures/inheritance_multi",
    "fixtures/trios2",
])
def test_dataframe_variants(fvars_df, fixture_name):
    ped_df, summary_df, vars_df = fvars_df(fixture_name)
    assert ped_df is not None
    assert summary_df is not None
    assert vars_df is not None

    print(summary_df.head())
    print(vars_df.head())

    # vars_df.set_index(["var_index", "allele_index"])
    sdf = summary_df.set_index(["var_index", "allele_index"])

    jdf = vars_df.join(sdf, on=("var_index", "allele_index"), rsuffix="_r")
    print(jdf.head())

    df = jdf[np.logical_and(
        jdf.chrom == "1",
        jdf.position == 11539)]

    print(df.head())


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
