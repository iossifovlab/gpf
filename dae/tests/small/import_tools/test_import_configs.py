# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import pathlib
from glob import glob
from typing import Any

import fsspec
import pytest
import pytest_mock
import yaml
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools import cli, import_tools
from dae.testing.alla_import import alla_gpf


@pytest.fixture
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
    resources_dir: pathlib.Path,
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
        import_config, base_input_dir=str(input_dir))

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
    gpf_instance: GPFInstance,
    resources_dir: pathlib.Path,
) -> None:
    input_dir = resources_dir / "vcf_import"
    config_fn = input_dir / "import_config_add_chrom_prefix.yaml"

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"] = {
        "work_dir": str(tmp_path),
    }

    project = import_tools.ImportProject.build_from_config(
        import_config,
        base_input_dir=str(input_dir),
        gpf_instance=gpf_instance)
    cli.run_with_project(project)

    files = os.listdir(tmp_path)
    assert len(files) != 0


def test_import_with_chrom_mapping(
    tmp_path: pathlib.Path,
    gpf_instance: GPFInstance,
    resources_dir: pathlib.Path,
) -> None:
    input_dir = resources_dir / "vcf_import"
    config_fn = input_dir / "import_config_chrom_mapping.yaml"

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"] = {
        "work_dir": str(tmp_path),
    }

    project = import_tools.ImportProject.build_from_config(
        import_config,
        base_input_dir=str(input_dir),
        gpf_instance=gpf_instance)
    cli.run_with_project(project)

    files = os.listdir(tmp_path)
    assert len(files) != 0


def test_add_chrom_prefix_is_propagated_to_the_loader(
    resources_dir: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
    gpf_instance: GPFInstance,
) -> None:
    config_fn = resources_dir / "vcf_import" \
        / "import_config_add_chrom_prefix.yaml"

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance)
    project = import_tools.ImportProject.build_from_file(config_fn)
    loader = project._get_variant_loader("vcf")
    assert loader._chrom_prefix == "chr"


def test_chrom_mapping_is_propagated_to_the_loader(
    resources_dir: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
    gpf_instance: GPFInstance,
) -> None:
    config_fn = resources_dir / "vcf_import" \
        / "import_config_chrom_mapping.yaml"

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance)
    project = import_tools.ImportProject.build_from_file(config_fn)
    loader = project._get_variant_loader("vcf")
    assert loader._adjust_chrom("1") == "chr1"
    assert loader._adjust_chrom("2") == "chr2"
    assert loader._adjust_chrom("3") == "chr3"
    assert loader._adjust_chrom("4") == "chr4"


@pytest.mark.parametrize("row_group_size, expected", [
    ("10000", 10_000),
    ("10k", 10_000),
    (None, 50_000),
])
def test_row_group_size(row_group_size: str | None, expected: int) -> None:
    import_config = {
        "id": "test_import",
        "input": {},
        "processing_config": {
            "work_dir": "",
            "denovo": {},
            "parquet_row_group_size": row_group_size,
        },
    }
    project = import_tools.ImportProject.build_from_config(import_config)
    assert project.get_row_group_size() == expected


def test_row_group_size_short_config() -> None:
    import_config = {
        "id": "test_import",
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
                "region_length": "300k",
            },
        },
        "partition_description": {
            "region_bin": {
                "region_length": "100M",
            },
        },
    }
    project = import_tools.ImportProject.build_from_config(config)

    config = project.import_config
    assert config["processing_config"]["denovo"]["region_length"] \
        == 300_000
    assert config["partition_description"]["region_bin"]["region_length"] \
        == 100_000_000


def test_shorthand_autosomes(
    gpf_instance: GPFInstance,
) -> None:
    config = {
        "id": "test_import",
        "input": {},
        "processing_config": {
            "vcf": {
                "region_length": 300,
                "chromosomes": ["autosomes"],
            },
        },
        "partition_description": {
            "region_bin": {
                "region_length": 100,
                "chromosomes": ["autosomesXY"],
            },
        },
    }
    project = import_tools.ImportProject.build_from_config(
        config, gpf_instance=gpf_instance)
    loader_chromosomes = project._get_loader_target_chromosomes("vcf")
    assert loader_chromosomes is not None
    # alla genome has 4 autosomes and X
    assert len(loader_chromosomes) == 4
    for i in range(1, 5):
        assert f"chr{i}" in loader_chromosomes

    part_desc = project.get_partition_descriptor()
    pd_chromosomes = part_desc.chromosomes
    # alla genome has 4 autosomes and X
    assert len(pd_chromosomes) == 5
    for i in range(1, 5):
        assert f"chr{i}" in pd_chromosomes
    assert "chrX" in pd_chromosomes


def test_shorthand_chromosomes() -> None:
    config: dict[str, Any] = {
        "id": "test_import",
        "input": {},
        "processing_config": {
            "denovo": {
                "chromosomes": "chr1, chr2",
            },
        },
        "partition_description": {
            "region_bin": {
                "region_length": 100,
                "chromosomes": "autosomes,X",
            },
        },
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
    project = import_tools.ImportProject.build_from_config(
        config, base_input_dir="")
    assert project.input_dir == ""


@pytest.mark.parametrize("input_dir", ["/input-dir", "input-dir"])
def test_project_input_dir(input_dir: str) -> None:
    config = {
        "id": "test_import",
        "input": {
            "input_dir": input_dir,
        },
    }
    project = import_tools.ImportProject.build_from_config(
        config, base_input_dir="/dir")
    assert project.input_dir == os.path.join("/dir", input_dir)


def test_get_genotype_storage_no_explicit_config(
    gpf_instance: GPFInstance,
) -> None:
    config = {
        "id": "test_import",
        "input": {},
        "gpf_instance": {
            "path": gpf_instance.dae_config.conf_dir,
        },
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
    resources_dir: pathlib.Path,
    gpf_instance: GPFInstance,
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
            },
        },
    }
    project = import_tools.ImportProject.build_from_config(
        config, gpf_instance=gpf_instance)
    with pytest.raises(
            ValueError,
            match="All chromosomes already have the prefix chr"):
        project._get_variant_loader("vcf")


def test_del_chrom_prefix_already_deleted(
    resources_dir: pathlib.Path,
    gpf_instance: GPFInstance,
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
            },
        },
    }
    project = import_tools.ImportProject.build_from_config(
        config, gpf_instance=gpf_instance)
    with pytest.raises(
            ValueError,
            match="Chromosomes already missing the prefix chr"):
        project._get_variant_loader("vcf")


def test_input_in_external_file(
    resources_dir: pathlib.Path,
) -> None:
    config_fn = resources_dir / "external_input" / "import_config.yaml"
    project = import_tools.ImportProject.build_from_file(config_fn)

    assert project.input_dir == f"{resources_dir}/external_input/files/"
    assert project.get_pedigree_filename() == \
        f"{resources_dir}/external_input/files/multivcf.ped"


def test_embedded_annotation_pipeline(
    t4c8_instance: GPFInstance,
) -> None:
    import_config = {
        "id": "test_import",
        "input": {},
        "annotation": [{
            "position_score": {
                "resource_id": "genomic_scores/score_one",
            },
        }],
        "gpf_instance": {
            "path": t4c8_instance.dae_config.conf_dir,
        },
    }
    project = import_tools.ImportProject.build_from_config(import_config)
    pipeline = project.build_annotation_pipeline()
    assert pipeline is not None
    assert len(pipeline.get_info()) == 1

    annotator_info = pipeline.get_info()[0]
    assert annotator_info.type == "position_score"
    assert annotator_info.parameters["resource_id"] == \
        "genomic_scores/score_one"


def test_annotation_file(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
) -> None:
    annotation = [{
        "position_score": {
            "resource_id": "genomic_scores/score_one",
        },
    }]
    annotation_fn = str(tmp_path / "annotation.yaml")
    with open(annotation_fn, "wt") as out_file:
        yaml.safe_dump(annotation, out_file)

    import_config = {
        "id": "test_import",
        "input": {},
        "annotation": {
            "file": "annotation.yaml",
        },
        "gpf_instance": {
            "path": t4c8_instance.dae_config.conf_dir,
        },
    }
    config_fn = str(tmp_path / "import_config.yaml")
    with open(config_fn, "wt") as out_file:
        yaml.safe_dump(import_config, out_file)

    project = import_tools.ImportProject.build_from_file(config_fn)
    pipeline = project.build_annotation_pipeline()
    assert pipeline is not None
    assert len(pipeline.get_info()) == 1

    annotator_info = pipeline.get_info()[0]
    assert annotator_info.type == "position_score"
    assert annotator_info.parameters["resource_id"] == \
        "genomic_scores/score_one"


def test_annotation_file_and_external_input_config(
    tmp_path: pathlib.Path, t4c8_instance: GPFInstance,
) -> None:
    annotation = [{
        "position_score": {
            "resource_id": "genomic_scores/score_one",
        },
    }]
    with open(str(tmp_path / "annotation.yaml"), "wt") as out_file:
        yaml.safe_dump(annotation, out_file)

    input_config: dict[str, Any] = {}
    with fsspec.open(str(tmp_path / "input" / "input.yaml"), "wt") as out_file:
        assert out_file is not None
        content = yaml.safe_dump(input_config)
        out_file.write(content)  # pyright: ignore[reportAttributeAccessIssue]

    import_config = {
        "id": "test_import",
        "input": {
            "file": "input/input.yaml",
        },
        "annotation": {
            "file": "annotation.yaml",
        },
        "gpf_instance": {
            "path": t4c8_instance.dae_config.conf_dir,
        },
    }
    config_fn = str(tmp_path / "import_config.yaml")
    with open(config_fn, "wt") as out_file:
        yaml.safe_dump(import_config, out_file)

    project = import_tools.ImportProject.build_from_file(config_fn)
    pipeline = project.build_annotation_pipeline()
    assert pipeline is not None
    assert len(pipeline.get_info()) == 1

    annotator_info = pipeline.get_info()[0]
    assert annotator_info.type == "position_score"
