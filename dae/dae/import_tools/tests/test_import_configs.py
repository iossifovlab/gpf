# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
from glob import glob

import pytest

from dae.import_tools import import_tools
from dae.configuration.gpf_config_parser import GPFConfigParser


@pytest.mark.parametrize("config_dir", ["denovo_import", "vcf_import",
                                        "cnv_import", "dae_import"])
def test_simple_import_config(tmpdir, gpf_instance_2019, config_dir, mocker):
    input_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources", config_dir)
    config_fn = os.path.join(input_dir, "import_config.yaml")

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"] = {
        "work_dir": str(tmpdir),
    }

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_2019)
    project = import_tools.ImportProject.build_from_config(
        import_config, input_dir)
    import_tools.run_with_project(project)

    files = os.listdir(tmpdir)
    assert len(files) != 0
    assert "test_import_pedigree" in files
    assert "test_import_variants" in files

    ped_parquets = os.listdir(os.path.join(tmpdir, "test_import_pedigree"))
    assert len(ped_parquets) != 0

    parquet_fns = os.path.join(tmpdir, "test_import_variants", "**/*.parquet")
    variants_bins = glob(parquet_fns, recursive=True)
    assert len(variants_bins) != 0


def test_import_with_add_chrom_prefix(tmpdir, gpf_instance_grch38, mocker):
    input_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources", "vcf_import")
    config_fn = os.path.join(input_dir, "import_config_add_chrom_prefix.yaml")

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"] = {
        "work_dir": str(tmpdir),
    }

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_grch38)
    project = import_tools.ImportProject.build_from_config(
        import_config, input_dir)
    import_tools.run_with_project(project)

    files = os.listdir(tmpdir)
    assert len(files) != 0


def test_add_chrom_prefix_is_propagated_to_the_loader(gpf_instance_2019):
    input_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources", "vcf_import")
    config_fn = os.path.join(input_dir, "import_config_add_chrom_prefix.yaml")

    project = import_tools.ImportProject.build_from_file(
        config_fn, gpf_instance=gpf_instance_2019)
    loader = project._get_variant_loader("vcf")
    assert loader._chrom_prefix == "chr"


def test_row_group_size():
    import_config = dict(
        input=dict(),
        processing_config=dict(
            work_dir="",
            denovo=dict(
            ),
        ),
        parquet_row_group_size=dict(
            denovo=10000,
            dae="10k",
        )
    )
    project = import_tools.ImportProject.build_from_config(import_config)
    assert project.get_row_group_size(
        import_tools.Bucket("denovo", "", "", 0)) == 10_000
    assert project.get_row_group_size(
        import_tools.Bucket("dae", "", "", 0)) == 10_000
    # 20_000 is the default value
    assert project.get_row_group_size(
        import_tools.Bucket("vcf", "", "", 0)) == 20_000


def test_row_group_size_short_config():
    import_config = dict(
        input=dict(),
        processing_config=dict(
            work_dir="",
            denovo="single_bucket",
        ),
    )
    project = import_tools.ImportProject.build_from_config(import_config)
    # 20_000 is the default value
    assert project.get_row_group_size(
        import_tools.Bucket("denovo", "", "", 0)) == 20_000


def test_shorthand_for_large_integers():
    config = dict(
        id="test_import",
        input=dict(),
        processing_config=dict(
            denovo=dict(
                region_length="300k"
            )
        ),
        partition_description=dict(
            region_bin=dict(
                region_length="100M"
            )
        )
    )
    project = import_tools.ImportProject.build_from_config(config)
    config = project.import_config
    assert config["processing_config"]["denovo"]["region_length"] \
        == 300_000
    assert config["partition_description"]["region_bin"]["region_length"] \
        == 100_000_000


def test_shorthand_autosomes():
    config = dict(
        id="test_import",
        input=dict(),
        processing_config=dict(
            vcf=dict(
                region_length=300,
                chromosomes=["autosomes"],
            )
        ),
        partition_description=dict(
            region_bin=dict(
                region_length=100,
                chromosomes=["autosomesXY"]
            )
        )
    )
    project = import_tools.ImportProject.build_from_config(config)
    loader_chromosomes = project._get_loader_target_chromosomes("vcf")
    assert len(loader_chromosomes) == 22 * 2
    for i in range(1, 23):
        assert str(i) in loader_chromosomes
        assert f"chr{i}" in loader_chromosomes

    pd_chromosomes = project.get_partition_description(work_dir="").chromosomes
    assert len(pd_chromosomes) == 22 * 2 + 4
    for i in range(1, 23):
        assert str(i) in pd_chromosomes
        assert f"chr{i}" in pd_chromosomes
    for i in ["X", "Y"]:
        assert str(i) in pd_chromosomes
        assert f"chr{i}" in pd_chromosomes


def test_shorthand_chromosomes():
    config = dict(
        id="test_import",
        input=dict(),
        processing_config=dict(
            denovo=dict(
                chromosomes="chr1, chr2"
            )
        ),
        partition_description=dict(
            region_bin=dict(
                region_length=100,
                chromosomes="autosomes,X"
            )
        )
    )
    project = import_tools.ImportProject.build_from_config(config)
    config = project.import_config
    assert config["processing_config"]["denovo"]["chromosomes"] \
        == ["chr1", "chr2"]
    chroms = config["partition_description"]["region_bin"]["chromosomes"]
    assert len(chroms) == 2 * 22 + 1
    assert chroms[-1] == "X"


def test_project_input_dir_default_value():
    config = dict(
        id="test_import",
        input=dict(),
    )
    project = import_tools.ImportProject.build_from_config(config, "")
    assert project.input_dir == ""


@pytest.mark.parametrize("input_dir", ["/input-dir", "input-dir"])
def test_project_input_dir(input_dir):
    config = dict(
        id="test_import",
        input=dict(
            input_dir=input_dir
        ),
    )
    project = import_tools.ImportProject.build_from_config(config, "/dir")
    assert project.input_dir == os.path.join("/dir", input_dir)
