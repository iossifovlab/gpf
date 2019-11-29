from dae.backends.impala.loader import ParquetLoader
from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesData


def test_partition_read(fixture_dirname):
    # ped_file = '/home/ivo/gpf/dae/dae/tests/fixtures/backends/partition.ped'
    ped_file = fixture_dirname('backends/partition.ped')

    ped_df = PedigreeReader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = ParquetLoader(
            families,
            fixture_dirname('backends/test_partition/_PARTITION_DESCRIPTION'))
    summaries = []
    genotypes = []
    for summary, genotype in loader.summary_genotypes_iterator():
        summaries.append(summary)
        genotypes.append(genotype)

    assert len(summaries) == len(genotypes)
    assert len(summaries) == 54
    assert any(s.chrom == '1' for s in summaries)
    assert any(s.chrom == '2' for s in summaries)
    assert not any(s.chrom == '3' for s in summaries)
    assert any(s.reference == 'G' for s in summaries)
    assert any(s.reference == 'CGGCTCGGAAGG' for s in summaries)


def test_partition_read_glob_region_1(fixture_dirname):
    # ped_file = '/home/ivo/gpf/dae/dae/tests/fixtures/backends/partition.ped'
    ped_file = fixture_dirname('backends/partition.ped')

    ped_df = PedigreeReader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = ParquetLoader(
            families,
            fixture_dirname('backends/test_partition/_PARTITION_DESCRIPTION'),
            ['region_bin=1_8/*/*/*/*'])
    summaries = []
    genotypes = []
    for summary, genotype in loader.summary_genotypes_iterator():
        summaries.append(summary)
        genotypes.append(genotype)

    assert len(summaries) == len(genotypes)
    assert len(summaries) == 42
    assert any(s.chrom == '1' for s in summaries)
    assert not any(s.chrom == '2' for s in summaries)
    assert not any(s.chrom == '3' for s in summaries)


def test_partition_read_glob_region_2(fixture_dirname):
    # ped_file = '/home/ivo/gpf/dae/dae/tests/fixtures/backends/partition.ped'
    ped_file = fixture_dirname('backends/partition.ped')

    ped_df = PedigreeReader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = ParquetLoader(
            families,
            fixture_dirname('backends/test_partition/_PARTITION_DESCRIPTION'),
            ['region_bin=1_8/*/*/*/*'])
    summaries = []
    genotypes = []
    for summary, genotype in loader.summary_genotypes_iterator():
        summaries.append(summary)
        genotypes.append(genotype)

    assert len(summaries) == len(genotypes)
    assert len(summaries) == 12
    assert not any(s.chrom == '1' for s in summaries)
    assert any(s.chrom == '2' for s in summaries)
    assert not any(s.chrom == '3' for s in summaries)
