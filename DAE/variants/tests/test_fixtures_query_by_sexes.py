'''
Created on Jul 3, 2018

@author: lubo
'''
import pytest


@pytest.mark.parametrize("variants", [
    "variants_vcf",
    # "variants_df",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,sexes,count", [
    ("fixtures/effects_trio_dad", 'male', 1),
    ("fixtures/effects_trio_dad", 'female', 1),
    ("fixtures/effects_trio_dad", 'male or female', 2),
    ("fixtures/trios2", 'female and not male', 9),
])
def test_fixture_query_by_sex(
        variants_impl, variants, fixture_name, sexes, count):
    vvars = variants_impl(variants)(fixture_name)
    # vvars = variants_df(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        sexes=sexes)
    vs = list(vs)
    print([(v, v.variant_in_members, v.variant_in_sexes) for v in vs])
    assert len(vs) == count


@pytest.mark.skip("raw_df needs fixing")
@pytest.mark.parametrize("fixture_name,sexes,count", [
    ("fixtures/effects_trio_dad", 'male', 1),
    ("fixtures/effects_trio_dad", 'female', 1),
    ("fixtures/effects_trio_dad", 'male or female', 2),
    ("fixtures/trios2", 'female and not male', 5),
])
def test_fixture_raw_df_query_by_sex_needs_fixing(
        variants_df, fixture_name, sexes, count):
    vvars = variants_df(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        sexes=sexes)
    vs = list(vs)
    print([(v, v.variant_in_members, v.variant_in_sexes) for v in vs])
    assert len(vs) == count
