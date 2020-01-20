import pytest
from dae.backends.impala.loader import ParquetLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData


@pytest.mark.xfail(reason='Parquet loader does not function properly')
def test_partition_read(fixture_dirname):
    # ped_file = '/home/ivo/gpf/dae/dae/tests/fixtures/backends/partition.ped'
    ped_file = fixture_dirname('backends/partition.ped')

    ped_df = FamiliesLoader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = ParquetLoader(
            families,
            fixture_dirname('backends/test_partition/'
                            'variants.parquet/_PARTITION_DESCRIPTION'))

    summary_variants = []
    for summary_variant, _ in loader.full_variants_iterator():
        summary_variants.append(summary_variant)

    assert len(summary_variants) == 54
    assert any(s.chrom == '1' for s in summary_variants)
    assert any(s.chrom == '2' for s in summary_variants)
    assert not any(s.chrom == '3' for s in summary_variants)
    assert any(s.reference == 'G' for s in summary_variants)
    assert any(s.reference == 'CGGCTCGGAAGG' for s in summary_variants)


@pytest.mark.xfail(reason='Parquet loader does not function properly')
def test_partition_read_glob_region_1(fixture_dirname):
    # ped_file = '/home/ivo/gpf/dae/dae/tests/fixtures/backends/partition.ped'
    ped_file = fixture_dirname('backends/partition.ped')

    ped_df = FamiliesLoader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = ParquetLoader(
            families,
            fixture_dirname('backends/test_partition/'
                            'variants.parquet/_PARTITION_DESCRIPTION'),
            ['region_bin=1_8/*/*/*/*'])
    summary_variants = []
    for summary_variant, _ in loader.full_variants_iterator():
        summary_variants.append(summary_variant)

    assert len(summary_variants) == 42
    assert any(s.chrom == '1' for s in summary_variants)
    assert not any(s.chrom == '2' for s in summary_variants)
    assert not any(s.chrom == '3' for s in summary_variants)


@pytest.mark.xfail(reason='Parquet loader does not function properly')
def test_partition_read_glob_region_2(fixture_dirname):
    # ped_file = '/home/ivo/gpf/dae/dae/tests/fixtures/backends/partition.ped'
    ped_file = fixture_dirname('backends/partition.ped')

    ped_df = FamiliesLoader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = ParquetLoader(
            families,
            fixture_dirname('backends/test_partition/'
                            'variants.parquet/_PARTITION_DESCRIPTION'),
            ['region_bin=2_9/*/*/*/*'])
    summary_variants = []
    for summary_variant, _ in loader.full_variants_iterator():
        summary_variants.append(summary_variant)

    assert len(summary_variants) == 12
    assert not any(s.chrom == '1' for s in summary_variants)
    assert any(s.chrom == '2' for s in summary_variants)
    assert not any(s.chrom == '3' for s in summary_variants)
