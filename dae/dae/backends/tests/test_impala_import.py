import os
from dae.backends.impala.parquet_io import VariantsParquetWriter


def test_impala_import_annotation(
        vcf_variants_loader, temp_filename):

    fvars = vcf_variants_loader('vcf_import/effects_trio')

    parquet_writer = VariantsParquetWriter(fvars)

    assert parquet_writer is not None

    print(parquet_writer.schema)
    print(dir(parquet_writer.schema))
    parquet_writer.save_variants_to_parquet(
        temp_filename
    )

    assert os.path.exists(temp_filename)
