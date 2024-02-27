# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import pathlib
from glob import glob
from typing import Callable, Any, Optional

import yaml
import pytest
import pytest_mock

import fsspec

from dae.import_tools import import_tools, cli
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.testing.alla_import import alla_gpf
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture()
def gpf_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(__name__)
    return alla_gpf(root_path)


@pytest.mark.parametrize("config_dir", ["denovo_import", "vcf_import",
                                        "cnv_import", "dae_import"])
def test_parquet_files_are_generated(
    tmp_path: pathlib.Path,
    gpf_instance: GPFInstance,
    config_dir: str,
    mocker: pytest_mock.MockerFixture,
    resources_dir: pathlib.Path
) -> None:
    input_dir = resources_dir / config_dir
    config_fn = input_dir / "import_config.yaml"

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"] = {
        "work_dir": str(tmp_path),
    }

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance)
    mocker.patch.object(import_tools.ImportProject, "_storage_type",
                        return_value="schema2")
    project = import_tools.ImportProject.build_from_config(
        import_config, str(input_dir))

    cli.run_with_project(project)

    files = os.listdir(tmp_path)
    assert len(files) != 0
    assert "test_import" in files

    files = os.listdir(os.path.join(tmp_path, "test_import"))

    assert "pedigree" in files
    assert "family" in files
    assert "summary" in files

    ped_parquets = os.listdir(
        os.path.join(tmp_path, "test_import", "pedigree"))
    assert len(ped_parquets) != 0

    parquet_fns = os.path.join(
        tmp_path, "test_import", "family", "**/*.parquet")
    family_bins = glob(parquet_fns, recursive=True)
    assert len(family_bins) != 0

    parquet_fns = os.path.join(
        tmp_path, "test_import", "summary", "**/*.parquet")
    summary_bins = glob(parquet_fns, recursive=True)
    assert len(summary_bins) != 0


def test_import_with_add_chrom_prefix(
    tmp_path: pathlib.Path,
    gpf_instance_grch38: GPFInstance,
    mocker: pytest_mock.MockerFixture,
    resources_dir: pathlib.Path
) -> None:
    input_dir = resources_dir / "vcf_import"
    config_fn = input_dir / "import_config_add_chrom_prefix.yaml"

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"] = {
        "work_dir": str(tmp_path),
    }

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_grch38)
    project = import_tools.ImportProject.build_from_config(
        import_config, str(input_dir))
    cli.run_with_project(project)

    files = os.listdir(tmp_path)
    assert len(files) != 0


def test_add_chrom_prefix_is_propagated_to_the_loader(
    resources_dir: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
    gpf_instance: GPFInstance
) -> None:
    config_fn = resources_dir / "vcf_import" \
        / "import_config_add_chrom_prefix.yaml"

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance)
    project = import_tools.ImportProject.build_from_file(config_fn)
    loader = project._get_variant_loader("vcf")
    assert loader._chrom_prefix == "chr"  # type: ignore


@pytest.mark.parametrize("row_group_size, expected", [
    ("10000", 10_000),
    ("10k", 10_000),
    (None, 50_000),
])
def test_row_group_size(row_group_size: Optional[str], expected: int) -> None:
    import_config = {
        "input": {},
        "processing_config": {
            "work_dir": "",
            "denovo": {},
            "parquet_row_group_size": row_group_size
        },
    }
    project = import_tools.ImportProject.build_from_config(import_config)
    assert project.get_row_group_size() == expected


def test_row_group_size_short_config() -> None:
    import_config = {
        "input": {},
        "processing_config": {
            "work_dir": "",
            "denovo": "single_bucket",
        },
    }
    project = import_tools.ImportProject.build_from_config(import_config)
    # 20_000 is the default value
    assert project.get_row_group_size() == 50_000


def test_shorthand_for_large_integers() -> None:
    config: dict[str, Any] = {
        "id": "test_import",
        "input": {},
        "processing_config": {
            "denovo": {
                "region_length": "300k"
            }
        },
        "partition_description": {
            "region_bin": {
                "region_length": "100M"
            }
        }
    }
    project = import_tools.ImportProject.build_from_config(config)

    config = project.import_config
    assert config["processing_config"]["denovo"]["region_length"] \
        == 300_000
    assert config["partition_description"]["region_bin"]["region_length"] \
        == 100_000_000


def test_shorthand_autosomes() -> None:
    config = {
        "id": "test_import",
        "input": {},
        "processing_config": {
            "vcf": {
                "region_length": 300,
                "chromosomes": ["autosomes"],
            }
        },
        "partition_description": {
            "region_bin": {
                "region_length": 100,
                "chromosomes": ["autosomesXY"]
            }
        }
    }
    project = import_tools.ImportProject.build_from_config(config)
    loader_chromosomes = project._get_loader_target_chromosomes("vcf")
    assert loader_chromosomes is not None
    assert len(loader_chromosomes) == 22 * 2
    for i in range(1, 23):
        assert str(i) in loader_chromosomes
        assert f"chr{i}" in loader_chromosomes

    part_desc = project.get_partition_descriptor()
    pd_chromosomes = part_desc.chromosomes
    assert len(pd_chromosomes) == 22 * 2 + 4
    for i in range(1, 23):
        assert str(i) in pd_chromosomes
        assert f"chr{i}" in pd_chromosomes
    for j in ["X", "Y"]:
        assert str(j) in pd_chromosomes
        assert f"chr{j}" in pd_chromosomes


def test_shorthand_chromosomes() -> None:
    config: dict[str, Any] = {
        "id": "test_import",
        "input": {},
        "processing_config": {
            "denovo": {
                "chromosomes": "chr1, chr2",
            }
        },
        "partition_description": {
            "region_bin": {
                "region_length": 100,
                "chromosomes": "autosomes,X"
            }
        }
    }
    project = import_tools.ImportProject.build_from_config(config)
    config = project.import_config
    assert config["processing_config"]["denovo"]["chromosomes"] \
        == ["chr1", "chr2"]
    chroms = config["partition_description"]["region_bin"]["chromosomes"]
    assert len(chroms) == 2 * 22 + 1
    assert chroms[-1] == "X"


def test_project_input_dir_default_value() -> None:
    config = {
        "id": "test_import",
        "input": {},
    }
    project = import_tools.ImportProject.build_from_config(config, "")
    assert project.input_dir == ""


@pytest.mark.parametrize("input_dir", ["/input-dir", "input-dir"])
def test_project_input_dir(input_dir: str) -> None:
    config = {
        "id": "test_import",
        "input": {
            "input_dir": input_dir
        },
    }
    project = import_tools.ImportProject.build_from_config(config, "/dir")
    assert project.input_dir == os.path.join("/dir", input_dir)


def test_get_genotype_storage_no_explicit_config(
    fixture_dirname: Callable
) -> None:
    config = {
        "id": "test_import",
        "input": {},
        "gpf_instance": {
            "path": fixture_dirname("")
        }
    }
    project = import_tools.ImportProject.build_from_config(config)
    genotype_storage = project.get_genotype_storage()
    assert genotype_storage is not None
    assert (
        genotype_storage.storage_id
        == project.get_gpf_instance().genotype_storages
        .get_default_genotype_storage().storage_id
    )


def test_add_chrom_prefix_already_present(
    resources_dir: pathlib.Path
) -> None:
    config = {
        "id": "test_import",
        "input": {
            "pedigree": {
                "file": f"{resources_dir}/vcf_import/multivcf.ped",
            },
            "vcf": {
                "files": [f"{resources_dir}/vcf_prefix/with_prefix.vcf"],
                "add_chrom_prefix": "chr",
            }
        }
    }
    project = import_tools.ImportProject.build_from_config(config)
    with pytest.raises(ValueError):
        project._get_variant_loader("vcf")


def test_del_chrom_prefix_already_deleted(
    resources_dir: pathlib.Path
) -> None:
    config = {
        "id": "test_import",
        "input": {
            "pedigree": {
                "file": f"{resources_dir}/vcf_import/multivcf.ped",
            },
            "vcf": {
                "files": [f"{resources_dir}/vcf_prefix/without_prefix.vcf"],
                "del_chrom_prefix": "chr",
            }
        }
    }
    project = import_tools.ImportProject.build_from_config(config)
    with pytest.raises(ValueError):
        project._get_variant_loader("vcf")


def test_input_in_external_file(
    resources_dir: pathlib.Path
) -> None:
    config_fn = resources_dir / "external_input" / "import_config.yaml"
    project = import_tools.ImportProject.build_from_file(config_fn)

    assert project.input_dir == f"{resources_dir}/external_input/files/"
    assert project.get_pedigree_filename() == \
        f"{resources_dir}/external_input/files/multivcf.ped"


def test_embedded_annotation_pipeline(fixture_dirname: Callable) -> None:
    import_config = {
        "input": {},
        "annotation": [{
            "np_score": {
                "resource_id": "hg19/CADD",
            }
        }],
        "gpf_instance": {
            "path": fixture_dirname("")
        }
    }
    project = import_tools.ImportProject.build_from_config(import_config)
    pipeline = project.build_annotation_pipeline()
    assert pipeline is not None
    assert len(pipeline.get_info()) == 1

    annotator_info = pipeline.get_info()[0]
    assert annotator_info.type == "np_score"
    assert annotator_info.parameters["resource_id"] == "hg19/CADD"


def test_annotation_file(
    tmp_path: pathlib.Path,
    fixture_dirname: Callable
) -> None:
    annotation = [{
        "np_score": {
            "resource_id": "hg19/CADD",
        }
    }]
    annotation_fn = str(tmp_path / "annotation.yaml")
    with open(annotation_fn, "wt") as out_file:
        yaml.safe_dump(annotation, out_file)

    import_config = {
        "input": {},
        "annotation": {
            "file": "annotation.yaml"
        },
        "gpf_instance": {
            "path": fixture_dirname("")
        }
    }
    config_fn = str(tmp_path / "import_config.yaml")
    with open(config_fn, "wt") as out_file:
        yaml.safe_dump(import_config, out_file)

    project = import_tools.ImportProject.build_from_file(config_fn)
    pipeline = project.build_annotation_pipeline()
    assert pipeline is not None
    assert len(pipeline.get_info()) == 1

    annotator_info = pipeline.get_info()[0]
    assert annotator_info.type == "np_score"
    assert annotator_info.parameters["resource_id"] == "hg19/CADD"


def test_annotation_file_and_external_input_config(
    tmp_path: pathlib.Path, fixture_dirname: Callable
) -> None:
    annotation = [{
        "np_score": {
            "resource_id": "hg19/CADD",
        }
    }]
    with open(str(tmp_path / "annotation.yaml"), "wt") as out_file:
        yaml.safe_dump(annotation, out_file)

    input_config: dict[str, Any] = {}
    with fsspec.open(str(tmp_path / "input" / "input.yaml"), "wt") as out_file:
        yaml.safe_dump(input_config, out_file)

    import_config = {
        "input": {
            "file": "input/input.yaml"
        },
        "annotation": {
            "file": "annotation.yaml"
        },
        "gpf_instance": {
            "path": fixture_dirname("")
        }
    }
    config_fn = str(tmp_path / "import_config.yaml")
    with open(config_fn, "wt") as out_file:
        yaml.safe_dump(import_config, out_file)

    project = import_tools.ImportProject.build_from_file(config_fn)
    pipeline = project.build_annotation_pipeline()
    assert pipeline is not None
    assert len(pipeline.get_info()) == 1

    annotator_info = pipeline.get_info()[0]
    assert annotator_info.type == "np_score"
