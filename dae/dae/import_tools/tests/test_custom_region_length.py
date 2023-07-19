# pylint: disable=W0621,C0114,C0116,W0212,W0613

from copy import deepcopy
import os
from os.path import join

import pytest
import pyarrow.parquet as pq

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.import_tools import import_tools, cli


def test_import_task_bin_size(gpf_instance_2019, tmpdir, mocker,
                              resources_dir):
    # Create the import config and set tmpdir as work_dir
    input_dir = resources_dir / "import_task_bin_size"
    config_fn = input_dir / "import_config.yaml"

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"]["work_dir"] = str(tmpdir)

    # Running the import
    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_2019)
    project = import_tools.ImportProject.build_from_config(
        import_config, input_dir)
    cli.run_with_project(project)

    # Assert the expected output files and dirs are created in the work_dir
    # (i.e. tmpdir)
    files = os.listdir(tmpdir)
    assert "test_import" in files

    study_dir = join(tmpdir, "test_import")
    assert set(os.listdir(study_dir)) == {
        "_PARTITION_DESCRIPTION",
        "_VARIANTS_SCHEMA",
        "family", "summary",
        "meta", "pedigree",
    }

    # This is the first output directory. Assert it has the right files
    # with the right content
    out_dir = join(
        study_dir,
        "summary/region_bin=1_0/frequency_bin=0")
    parquet_files = [
        "merged_region_bin_1_0_frequency_bin_0.parquet",
    ]
    assert set(os.listdir(out_dir)) == set(parquet_files)
    _assert_variants(
        join(out_dir, parquet_files[0]),
        bucket_index=[
            0, 0, 0, 0, 0, 0,
            1, 1, 1, 1,
            3, 3,
        ],
        positions=[
            123, 123, 150, 150, 30000000, 30000000,
            30000001, 30000001, 40000000, 40000000,
            99999999, 99999999
        ]
    )

    # Same for the second directory
    out_dir = join(
        study_dir,
        "summary/region_bin=1_1/frequency_bin=0")
    parquet_files = [
        "merged_region_bin_1_1_frequency_bin_0.parquet",
    ]
    assert set(os.listdir(out_dir)) == set(parquet_files)
    _assert_variants(
        join(out_dir, parquet_files[0]),
        bucket_index=[
            3, 3, 3, 3,
            4, 4,
        ],
        positions=[
            100000000, 100000000, 120000000, 120000000,
            120000001, 120000001,
        ]
    )


def _assert_variants(parquet_fn, bucket_index, positions):
    variants = pq.read_table(parquet_fn).to_pandas()
    assert variants.shape[0] == len(positions)
    assert (variants.bucket_index == bucket_index).all()
    assert (variants.position == positions).all()


def test_bucket_generation(gpf_instance_2019, mocker):
    import_config = {
        "input": {
            "pedigree": {
                "file": join(_input_dir, "pedigree.ped"),
            },
            "denovo": {
                "files": [join(_input_dir, "single_chromosome_variants.tsv")],
                "person_id": "spid",
                "chrom": "chrom",
                "pos": "pos",
                "ref": "ref",
                "alt": "alt",
            }
        },
        "processing_config": {
            "work_dir": "",
            "denovo": {
                "chromosomes": ["1"],
                "region_length": 70_000_000
            }
        },
        "partition_description": {
            "region_bin": {
                "chromosomes": ["1"],
                "region_length": 100_000_000
            }
        }
    }
    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_2019)
    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 4
    assert buckets[0].regions == ["1:1-70000000"]
    assert buckets[1].regions == ["1:70000001-140000000"]
    assert buckets[2].regions == ["1:140000001-210000000"]
    assert buckets[3].regions == ["1:210000001-249250621"]


def test_bucket_generation_chrom_mismatch(gpf_instance_short, mocker):
    import_config = {
        "input": {
            "pedigree": {
                "file": join(_input_dir, "pedigree.ped"),
            },
            "denovo": {
                "files": [join(_input_dir, "single_chromosome_variants.tsv")],
                "person_id": "spid",
                "chrom": "chrom",
                "pos": "pos",
                "ref": "ref",
                "alt": "alt",
            }
        },
        "processing_config": {
            "work_dir": "",
            "denovo": {
                "chromosomes": ["2"],
                "region_length": 140_000
            }
        },
        "partition_description": {
            "region_bin": {
                "chromosomes": ["1"],
                "region_length": 150_000
            }
        }
    }
    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_short)
    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project.get_import_variants_buckets())
    assert len(buckets) == 3
    for i in range(3):
        assert buckets[i].region_bin == f"other_{i}"
    assert buckets[0].regions == ["1:1-140000"]
    assert buckets[1].regions == ["1:140001-280000"]
    assert buckets[2].regions == ["1:280001-300000"]


_input_dir = join(
    os.path.dirname(os.path.realpath(__file__)),
    "resources", "import_task_bin_size")
_denovo_multi_chrom_config = {
    "input": {
        "pedigree": {
            "file": join(_input_dir, "pedigree.ped")
        },
        "denovo": {
            "files": [join(_input_dir, "multi_chromosome_variants.tsv")],
            "person_id": "spid",
            "chrom": "chrom",
            "pos": "pos",
            "ref": "ref",
            "alt": "alt",
        }
    },
    "processing_config": {
        "work_dir": "",
    },
    "partition_description": {
        "region_bin": {
            "chromosomes": ["chr1"],
            "region_length": 100000000
        }
    }
}


@pytest.mark.parametrize("add_chrom_prefix", [None, "chr"])
def test_single_bucket_generation(add_chrom_prefix, gpf_instance_2019, mocker):
    import_config = deepcopy(_denovo_multi_chrom_config)

    import_config[
        "processing_config"]["denovo"] = "single_bucket"  # type: ignore

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_2019)
    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 1
    assert buckets[0].regions == [None]


def test_single_bucket_is_default_when_missing_processing_config(
        gpf_instance_2019, mocker):
    import_config = deepcopy(_denovo_multi_chrom_config)
    assert "denovo" not in import_config["processing_config"]  # type: ignore

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_2019)
    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 1
    assert buckets[0].regions == [None]


@pytest.mark.parametrize("add_chrom_prefix", [None, "chr"])
def test_chromosome_bucket_generation(add_chrom_prefix, gpf_instance_2019,
                                      mocker):
    import_config = deepcopy(_denovo_multi_chrom_config)
    import_config["processing_config"]["denovo"] = "chromosome"  # type: ignore
    if add_chrom_prefix:
        import_config["input"]["denovo"][  # type: ignore
            "add_chrom_prefix"] = add_chrom_prefix
        prefix = add_chrom_prefix
    else:
        prefix = ""

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_2019)
    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 5
    assert buckets[0].regions == [f"{prefix}1"]
    assert buckets[1].regions == [f"{prefix}2"]
    assert buckets[2].regions == [f"{prefix}3"]
    assert buckets[3].regions == [f"{prefix}4"]
    assert buckets[4].regions == [f"{prefix}5"]


def test_chromosome_list_bucket_generation(gpf_instance_2019, mocker):
    import_config = deepcopy(_denovo_multi_chrom_config)
    import_config["processing_config"]["denovo"] = {  # type: ignore
        "chromosomes": ["1", "2", "3"]
    }

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_2019)
    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins("denovo"))
    assert len(buckets) == 4
    assert buckets[0].regions == ["1"]
    assert buckets[1].regions == ["2"]
    assert buckets[2].regions == ["3"]
    assert buckets[3].region_bin == "other_0"
    assert buckets[3].regions == ["4", "5"]
