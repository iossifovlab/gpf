from dae.backends.import_commons import construct_import_annotation_pipeline
from dae.backends.impala.parquet_io import VariantsParquetWriter


def test_f1_all_unknown_import(
        variants_vcf, temp_filename, dae_config_fixture, genomes_db):
    fvars = variants_vcf("backends/f1_test_901923")
    annotation_pipeline = \
        construct_import_annotation_pipeline(dae_config_fixture, genomes_db)

    variants_writer = VariantsParquetWriter(
        fvars.families,
        fvars.full_variants_iterator(),
        annotation_pipeline=annotation_pipeline)

    variants_writer.save_variants_to_parquet(
        temp_filename,
        bucket_index=0,
        rows=100000)
