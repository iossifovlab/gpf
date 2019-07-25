import os
from backends.impala.parquet_io import VariantsParquetWriter


def test_impala_import_annotation(
        vcf_import_raw, annotation_pipeline_internal, temp_filename):
    assert annotation_pipeline_internal

    fvars = vcf_import_raw

    parquet_writer = VariantsParquetWriter(
        fvars.families,
        fvars.full_variants_iterator(),
        annotation_pipeline_internal)

    assert parquet_writer is not None

    print(parquet_writer.schema)
    print(dir(parquet_writer.schema))
    print(parquet_writer.schema.names)
    parquet_writer.save_variants_to_parquet(
        temp_filename
    )

    assert os.path.exists(temp_filename)
