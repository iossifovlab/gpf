'''
Created on Mar 29, 2018

@author: lubo
'''
import pytest

from dae.RegionOperations import Region
from dae.utils.vcf_utils import mat2str
from dae.backends.impala.parquet_io import VariantsParquetWriter


@pytest.mark.parametrize('variants', [
    'variants_vcf',
    'variants_impala',
    'variants_mem'
])
@pytest.mark.parametrize("region,count,members", [
    (Region('1', 11500, 11500), 1, ['mom1', None, None]),
    (Region('1', 11501, 11501), 1, ['mom1', None, 'ch1']),
    (Region('1', 11502, 11502), 1, [None, None, 'ch1']),
    (Region('1', 11503, 11503), 1, ['mom1', 'dad1', 'ch1']),
])
def test_variant_in_members(variants_impl, variants, region, count, members):
    fvars = variants_impl(variants)("backends/unknown_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st))
        for aa in v.alt_alleles:
            print(aa, aa.variant_in_members)
            assert list(aa.variant_in_members) == members


@pytest.mark.parametrize('variants', [
    'variants_vcf',
])
@pytest.mark.parametrize("fixture_name", [
    "backends/f1_test_901923",
])
def test_full_variants_iterator_parquet_storage_unknown_variants(
        variants_impl, variants, fixture_name):

    fvars = variants_impl(variants)(fixture_name)
    assert fvars is not None

    parquet_writer = VariantsParquetWriter(fvars)
    table_iterator = parquet_writer.variants_table()
    for t in table_iterator:
        print(t)
