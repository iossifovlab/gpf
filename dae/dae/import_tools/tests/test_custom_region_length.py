# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import pathlib
from copy import deepcopy
from os.path import join
from typing import Optional

import pyarrow.parquet as pq
import pytest

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools import cli, import_tools
from dae.testing.acgt_import import acgt_gpf


@pytest.fixture()
def gpf_fixture(tmp_path: pathlib.Path) -> GPFInstance:
    return acgt_gpf(tmp_path / "gpf")


def test_import_task_bin_size(
    gpf_fixture: GPFInstance,
    tmp_path: pathlib.Path,
    resources_dir: pathlib.Path,
) -> None:
    # Create the import config and set tmpdir as work_dir
    input_dir = resources_dir / "import_task_bin_size"
    config_fn = input_dir / "import_config.yaml"

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"]["work_dir"] = str(tmp_path)

    # Running the import
    project = import_tools.ImportProject.build_from_config(
        import_config, str(input_dir), gpf_instance=gpf_fixture)
    cli.run_with_project(project)

    # Assert the expected output files and dirs are created in the work_dir
    # (i.e. tmpdir)
    files = os.listdir(tmp_path)
    assert "test_import" in files

    study_dir = join(tmp_path, "test_import")
    assert set(os.listdir(study_dir)) == {
        "family", "summary",
        "meta", "pedigree",
    }

    # This is the first output directory. Assert it has the right files
    # with the right content
    out_dir = join(
        study_dir,
        "summary/region_bin=chr1_0/frequency_bin=0")
    parquet_files = [
        "merged_region_bin_chr1_0_frequency_bin_0.parquet",
    ]

    assert set(os.listdir(out_dir)) == set(parquet_files)
    _assert_variants(
        join(out_dir, parquet_files[0]),
        bucket_index=[
            0, 0, 0,
            1, 1,
            2,
        ],
        positions=[
            1, 2, 10,
            21, 22, 59,
        ],
    )

    # Same for the second directory
    out_dir = join(
        study_dir,
        "summary/region_bin=chr1_1/frequency_bin=0")
    parquet_files = [
        "merged_region_bin_chr1_1_frequency_bin_0.parquet",
    ]
    assert set(os.listdir(out_dir)) == set(parquet_files)
    _assert_variants(
        join(out_dir, parquet_files[0]),
        bucket_index=[
            2, 3, 3,
        ],
        positions=[
            60, 70, 71,
        ],
    )


def _assert_variants(
    parquet_fn: str,
    bucket_index: list[int],
    positions: list[int],
) -> None:
    variants = pq.read_table(parquet_fn).to_pandas()

    assert variants.shape[0] == len(positions)
    assert (variants.bucket_index == bucket_index).all()
    assert (variants.position == positions).all()


def test_bucket_generation(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "input": {
            "pedigree": {
                "file": join(_input_dir, "pedigree.ped"),
            },
            "denovo": {
                "files": [join(_input_dir, "single_chromosome_variants.tsv")],
                "family_id": "familyId",
                "chrom": "chrom",
                "pos": "pos",
                "ref": "ref",
                "alt": "alt",
                "genotype": "genotype",
            },
        },
        "processing_config": {
            "work_dir": "",
            "denovo": {
                "chromosomes": ["chr1"],
                "region_length": 15,
            },
        },
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 50,
            },
        },
    }
    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 7
    assert buckets[0].regions == ["chr1:1-15"]
    assert buckets[1].regions == ["chr1:16-30"]
    assert buckets[2].regions == ["chr1:31-45"]
    assert buckets[3].regions == ["chr1:46-60"]
    assert buckets[4].regions == ["chr1:61-75"]
    assert buckets[5].regions == ["chr1:76-90"]
    assert buckets[6].regions == ["chr1:91-100"]


def test_bucket_generation_no_processing_region_length(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "input": {
            "pedigree": {
                "file": join(_input_dir, "pedigree.ped"),
            },
            "denovo": {
                "files": [join(_input_dir, "single_chromosome_variants.tsv")],
                "family_id": "familyId",
                "chrom": "chrom",
                "pos": "pos",
                "ref": "ref",
                "alt": "alt",
                "genotype": "genotype",
            },
        },
        "processing_config": {
            "work_dir": "",
            # "denovo": {
            #     "chromosomes": ["chr1"],
            #     "region_length": 15
            # }
        },
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 50,
            },
        },
    }
    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 1
    assert buckets[0].regions == [None]


def test_bucket_generation_chrom_mismatch(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "input": {
            "pedigree": {
                "file": join(_input_dir, "pedigree.ped"),
            },
            "denovo": {
                "files": [join(_input_dir, "single_chromosome_variants.tsv")],
                "family_id": "familyId",
                "chrom": "chrom",
                "pos": "pos",
                "ref": "ref",
                "alt": "alt",
                "genotype": "genotype",
            },
        },
        "processing_config": {
            "work_dir": "",
            "denovo": {
                "chromosomes": ["chr2"],
                "region_length": 40,
            },
        },
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 60,
            },
        },
    }

    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    buckets = list(project.get_import_variants_buckets())
    assert len(buckets) == 3
    for i in range(3):
        assert buckets[i].region_bin == f"other_{i}"
    assert buckets[0].regions == ["chr1:1-40"]
    assert buckets[1].regions == ["chr1:41-80"]
    assert buckets[2].regions == ["chr1:81-100"]


_input_dir = join(
    os.path.dirname(os.path.realpath(__file__)),
    "resources", "import_task_bin_size")
_denovo_multi_chrom_config = {
    "input": {
        "pedigree": {
            "file": join(_input_dir, "pedigree.ped"),
        },
        "denovo": {
            "files": [join(_input_dir, "multi_chromosome_variants.tsv")],
            "family_id": "familyId",
            "chrom": "chrom",
            "pos": "pos",
            "ref": "ref",
            "alt": "alt",
            "genotype": "genotype",
        },
    },
    "processing_config": {
        "work_dir": "",
    },
    "partition_description": {
        "region_bin": {
            "chromosomes": ["chr1"],
            "region_length": 40,
        },
    },
}


@pytest.mark.parametrize("add_chrom_prefix", [None, "chr"])
def test_single_bucket_generation(
    add_chrom_prefix: Optional[str],
    gpf_fixture: GPFInstance,
) -> None:
    import_config = deepcopy(_denovo_multi_chrom_config)

    import_config[
        "processing_config"]["denovo"] = "single_bucket"  # type: ignore

    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 1
    assert buckets[0].regions == [None]


def test_single_bucket_is_default_when_missing_processing_config(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = deepcopy(_denovo_multi_chrom_config)
    assert "denovo" not in import_config["processing_config"]  # type: ignore

    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 1
    assert buckets[0].regions == [None]


def test_chromosome_bucket_generation(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = deepcopy(_denovo_multi_chrom_config)
    import_config["processing_config"]["denovo"] = "chromosome"  # type: ignore

    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 2
    assert buckets[0].regions == ["chr1"]
    assert buckets[1].regions == ["chr2"]


def test_chromosome_list_bucket_generation(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = deepcopy(_denovo_multi_chrom_config)
    import_config["processing_config"]["denovo"] = {  # type: ignore
        "chromosomes": ["chr1"],
    }
    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 2
    assert buckets[0].regions == ["chr1"]
    assert buckets[1].regions == ["chr2"]
    assert buckets[1].region_bin == "other_0"
