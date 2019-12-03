from dae.backends.impala.parquet_io import VariantsParquetWriter


def test_f1_all_unknown_import(
        vcf_variants_loader, temp_filename, dae_config_fixture, genomes_db):
    fvars = vcf_variants_loader("backends/f1_test_901923")
    assert fvars.annotation_schema is not None

    variants_writer = VariantsParquetWriter(fvars)
    variants_writer.save_variants_to_parquet(temp_filename)
