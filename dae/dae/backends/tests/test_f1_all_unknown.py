from dae.backends.impala.parquet_io import VariantsParquetWriter


def test_f1_all_unknown_import(
        variants_vcf, temp_filename, dae_config_fixture, genomes_db):
    fvars = variants_vcf("backends/f1_test_901923")
    assert fvars.annotation_schema is not None

    variants_writer = VariantsParquetWriter(fvars)
    variants_writer.save_variants_to_parquet(temp_filename)
