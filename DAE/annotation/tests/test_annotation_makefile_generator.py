from .utils import relative_to_this_test_folder
from annotation.annotation_makefile_generator import VariantDBConfig
from pprint import pprint


def test_parse_generator_config():
    data_dir = relative_to_this_test_folder("fixtures/hg38_variants_config/")

    config = VariantDBConfig._parse_variants_db_config(data_dir)
    pprint(config)
    pprint(config.keys())

    denovo_files, transmitted_files = \
        VariantDBConfig._collect_studies(config)
    pprint(denovo_files)
    pprint(transmitted_files)

