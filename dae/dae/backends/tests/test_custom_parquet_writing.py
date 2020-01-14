from dae.backends.impala.parquet_io import VariantsParquetWriter
from dae.backends.impala.parquet_io import ParquetPartitionDescriptor


def test_custom_parquet_writing(vcf_variants_loader):
    fvars = vcf_variants_loader('vcf_import/effects_trio')

    partition_desc = ParquetPartitionDescriptor(['2'], 10, 10)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           '/tmp/variant-test-dataset2')

    assert parquet_writer is not None

    # print(parquet_writer.schema)
    # print(dir(parquet_writer.schema))
    # temp_filename = '/tmp/variant-test-dataset2'
    parquet_writer.write_dataset()

    # assert os.path.exists(temp_filename)
