from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.import_config import import_config_schema
import pytest
import os
from glob import glob
from dae.import_tools import import_tools


@pytest.mark.parametrize("config_dir", ["denovo_import", "vcf_import",
                                        "cnv_import", "dae_import"])
def test_denovo_import_config(tmpdir, gpf_instance_2019, config_dir):
    input_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources", config_dir)
    config_fn = os.path.join(input_dir, "import_config.yaml")

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config = GPFConfigParser.validate_config(import_config,
                                                    import_config_schema)
    import_config["input"]["input_dir"] = input_dir
    import_config["processing_config"] = {
        "work_dir": tmpdir,
    }

    import_tools.run(import_config, gpf_instance=gpf_instance_2019)

    files = os.listdir(tmpdir)
    assert len(files) != 0
    assert "test_import_pedigree" in files
    assert "test_import_variants" in files

    ped_parquets = os.listdir(os.path.join(tmpdir, "test_import_pedigree"))
    assert len(ped_parquets) != 0

    parquet_fns = os.path.join(tmpdir, "test_import_variants", "**/*.parquet")
    variants_bins = glob(parquet_fns, recursive=True)
    assert len(variants_bins) != 0


def test_add_chrom_prefix():
    input_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources", "vcf_import")
    config_fn = os.path.join(input_dir, "import_config_add_chrom_prefix.yaml")

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config = GPFConfigParser.validate_config(import_config,
                                                    import_config_schema)
    import_config["input"]["input_dir"] = input_dir

    project = import_tools.ImportProject(import_config)
    loader = project._get_variant_loader("vcf")
    assert loader._chrom_prefix == "chr"
