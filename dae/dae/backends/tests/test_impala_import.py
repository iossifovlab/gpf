import os
from dae.backends.impala.parquet_io import VariantsParquetWriter


def test_impala_import_annotation(
        variants_vcf, temp_filename):

    fvars = variants_vcf('vcf_import/effects_trio')

    parquet_writer = VariantsParquetWriter(fvars)

    assert parquet_writer is not None

    print(parquet_writer.schema)
    print(dir(parquet_writer.schema))
    # print(parquet_writer.schema.names)
    parquet_writer.save_variants_to_parquet(
        temp_filename
    )

    assert os.path.exists(temp_filename)
