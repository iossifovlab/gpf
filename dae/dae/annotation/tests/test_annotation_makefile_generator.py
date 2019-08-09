from .conftest import relative_to_this_test_folder
from dae.annotation.annotation_makefile_generator import VariantDBConfig


def test_parse_generator_config():
    data_dir = relative_to_this_test_folder("fixtures/hg38_variants_config/")

    config = VariantDBConfig._parse_variants_db_config(data_dir)
    denovo_files, transmitted_files = \
        VariantDBConfig._collect_studies(config)

    assert len(transmitted_files) == 4
    assert len(denovo_files) == 24
