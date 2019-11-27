from dae.backends.impala.loader import ParquetLoader
from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesData


def test_reading_partition():
    ped_file = '/home/ivo/gpf/dae/dae/tests/fixtures/backends/partition.ped'

    ped_df = PedigreeReader.flexible_pedigree_read(ped_file)
    families = FamiliesData.from_pedigree_df(ped_df)

    loader = ParquetLoader(
            families,
            '/tmp/dataset-partition-test/_PARTITION_DESCRIPTION')
    for summary, genotype in loader.summary_genotypes_iterator():
        print(summary, genotype)
