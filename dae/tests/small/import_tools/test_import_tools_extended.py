# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Extended tests for import_tools module."""
import pathlib
import sys
from typing import Any

import pytest
from box import Box
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.import_tools import (
    Bucket,
    ImportConfigNormalizer,
    ImportProject,
    construct_import_annotation_pipeline,
    construct_import_annotation_pipeline_config,
    get_import_storage_types,
    register_import_storage_factory,
    save_study_config,
)
from dae.testing.alla_import import alla_gpf
from dae.testing.foobar_import import foobar_gpf


@pytest.fixture
def gpf_fixture(tmp_path: pathlib.Path) -> GPFInstance:
    return alla_gpf(tmp_path)


def test_bucket_str_representation() -> None:
    bucket = Bucket(
        type="vcf",
        region_bin="chr1_0",
        regions=["chr1:1-1000000"],
        index=100_001,
    )
    assert str(bucket) == "Bucket(vcf,chr1_0,chr1:1-1000000,100001)"


def test_bucket_with_multiple_regions() -> None:
    bucket = Bucket(
        type="denovo",
        region_bin="chr1_0",
        regions=["chr1:1-1000000", "chr2:1-1000000"],
        index=1,
    )
    result = str(bucket)
    assert "chr1:1-1000000;chr2:1-1000000" in result


def test_bucket_with_empty_regions() -> None:
    bucket = Bucket(
        type="vcf",
        region_bin="all",
        regions=[],
        index=100_000,
    )
    result = str(bucket)
    assert "all" in result


def test_import_project_study_id(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study_123",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.study_id == "test_study_123"


def test_import_project_input_dir_default(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config,
        base_input_dir="/base/path",
        gpf_instance=gpf_fixture)
    # fs_utils.join adds trailing slash
    assert project.input_dir == "/base/path/"


def test_import_project_input_dir_custom(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "input_dir": "custom_input",
        },
    }
    project = ImportProject.build_from_config(
        import_config,
        base_input_dir="/base/path",
        gpf_instance=gpf_fixture)
    assert project.input_dir == "/base/path/custom_input"


def test_import_project_include_reference_default(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.include_reference is False


def test_import_project_include_reference_true(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
        "processing_config": {
            "include_reference": True,
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.include_reference is True


def test_import_project_annotation_batch_size_default(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.get_processing_annotation_batch_size() == 0


def test_import_project_annotation_batch_size_custom(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
        "processing_config": {
            "annotation_batch_size": 1000,
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.get_processing_annotation_batch_size() == 1000


def test_import_project_parquet_dataset_dir_none(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.get_processing_parquet_dataset_dir() is None


def test_import_project_get_parquet_dataset_dir(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config,
        base_input_dir="/base/path",
        gpf_instance=gpf_fixture)
    # Should return work_dir/study_id when no processing parquet dir
    result = project.get_parquet_dataset_dir()
    assert result.endswith("test_study")


def test_import_project_has_variants_false(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.has_variants() is False


def test_import_project_has_variants_true_with_vcf(
    gpf_fixture: GPFInstance,
) -> None:
    import_config: dict[str, Any] = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project.has_variants() is True


def test_import_project_get_variant_loader_raises_without_type(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    with pytest.raises(ValueError, match="loader_type or bucket is required"):
        project.get_variant_loader()


def test_import_project_del_loader_prefix() -> None:
    params = {
        "vcf_chromosomes": "1;2;3",
        "vcf_denovo_mode": "denovo",
        "vcf_include_reference": True,
        "other_param": None,
    }
    result = ImportProject.del_loader_prefix(params, "vcf_")
    assert result == {
        "chromosomes": "1;2;3",
        "denovo_mode": "denovo",
        "include_reference": True,
    }
    assert "other_param" not in result


def test_import_project_del_loader_prefix_no_prefix() -> None:
    params = {
        "chromosomes": "1;2;3",
        "denovo_mode": "denovo",
    }
    result = ImportProject.del_loader_prefix(params, "vcf_")
    assert result == params


def test_import_config_normalizer_int_shorthand_k() -> None:
    normalizer = ImportConfigNormalizer()
    assert normalizer._int_shorthand("10k") == 10_000
    assert normalizer._int_shorthand("10K") == 10_000


def test_import_config_normalizer_int_shorthand_m() -> None:
    normalizer = ImportConfigNormalizer()
    assert normalizer._int_shorthand("5m") == 5_000_000
    assert normalizer._int_shorthand("5M") == 5_000_000


def test_import_config_normalizer_int_shorthand_g() -> None:
    normalizer = ImportConfigNormalizer()
    assert normalizer._int_shorthand("2g") == 2_000_000_000
    assert normalizer._int_shorthand("2G") == 2_000_000_000


def test_import_config_normalizer_int_shorthand_plain_int() -> None:
    normalizer = ImportConfigNormalizer()
    assert normalizer._int_shorthand(42) == 42
    assert normalizer._int_shorthand("42") == 42


def test_import_config_normalizer_normalize_chrom_list_string() -> None:
    normalizer = ImportConfigNormalizer()
    result = normalizer._normalize_chrom_list("chr1, chr2, chr3")
    assert result == ["chr1", "chr2", "chr3"]


def test_import_config_normalizer_normalize_chrom_list_list() -> None:
    normalizer = ImportConfigNormalizer()
    result = normalizer._normalize_chrom_list(["chr1", "chr2", "chr3"])
    assert result == ["chr1", "chr2", "chr3"]


def test_import_config_normalizer_expand_autosomes() -> None:
    normalizer = ImportConfigNormalizer()
    result = normalizer._expand_chromosomes(["autosomes"])
    # Should contain both 1-22 and chr1-chr22
    assert "1" in result
    assert "chr1" in result
    assert "22" in result
    assert "chr22" in result
    # Should not contain X or Y
    assert "X" not in result
    assert "chrX" not in result


def test_import_config_normalizer_expand_autosomes_xy() -> None:
    normalizer = ImportConfigNormalizer()
    result = normalizer._expand_chromosomes(["autosomesXY"])
    # Should contain 1-22, X, Y and chr versions
    assert "1" in result
    assert "chr1" in result
    assert "X" in result
    assert "chrX" in result
    assert "Y" in result
    assert "chrY" in result


def test_import_config_normalizer_expand_chromosomes_mixed() -> None:
    normalizer = ImportConfigNormalizer()
    result = normalizer._expand_chromosomes(["chrM", "autosomes", "chrZ"])
    assert "chrM" in result
    assert "chrZ" in result
    assert "1" in result
    assert "chr1" in result


def test_construct_annotation_pipeline_config_default(
    gpf_fixture: GPFInstance,
) -> None:
    config = construct_import_annotation_pipeline_config(gpf_fixture)
    assert config is not None
    assert isinstance(config, list)


def test_construct_annotation_pipeline_config_with_file(
    tmp_path: pathlib.Path,
    gpf_fixture: GPFInstance,
) -> None:
    annotation_file = tmp_path / "annotation.yaml"
    annotation_file.write_text("""
    - position_score: genomic_context
    """)

    config = construct_import_annotation_pipeline_config(
        gpf_fixture, str(annotation_file))
    assert config is not None
    assert isinstance(config, list)


def test_construct_annotation_pipeline(
    gpf_fixture: GPFInstance,
) -> None:
    pipeline = construct_import_annotation_pipeline(gpf_fixture)
    assert pipeline is not None


def test_construct_annotation_pipeline_with_work_dir(
    tmp_path: pathlib.Path,
    gpf_fixture: GPFInstance,
) -> None:
    work_dir = tmp_path / "work"
    pipeline = construct_import_annotation_pipeline(
        gpf_fixture, work_dir=work_dir)
    assert pipeline is not None


def test_save_study_config_new_file(
    tmp_path: pathlib.Path,
) -> None:
    dae_config = Box({
        "studies": {
            "dir": str(tmp_path / "studies"),
        },
    })
    study_id = "test_study"
    study_config = "id: test_study\nname: Test Study\n"

    save_study_config(dae_config, study_id, study_config)

    expected_path = tmp_path / "studies" / "test_study" / "test_study.yaml"
    assert expected_path.exists()
    assert study_config in expected_path.read_text()


def test_save_study_config_existing_file_no_force(
    tmp_path: pathlib.Path,
) -> None:
    studies_dir = tmp_path / "studies" / "test_study"
    studies_dir.mkdir(parents=True)
    config_file = studies_dir / "test_study.yaml"
    original_content = "id: test_study\noriginal: true\n"
    config_file.write_text(original_content)

    dae_config = Box({
        "studies": {
            "dir": str(tmp_path / "studies"),
        },
    })
    study_id = "test_study"
    new_config = "id: test_study\nupdated: true\n"

    save_study_config(dae_config, study_id, new_config, force=False)

    # Original file should remain unchanged
    assert config_file.read_text() == original_content
    # Backup file should contain the new config
    backup_files = list(studies_dir.glob("test_study.*"))
    assert len(backup_files) == 2  # original + backup


def test_save_study_config_existing_file_force(
    tmp_path: pathlib.Path,
) -> None:
    studies_dir = tmp_path / "studies" / "test_study"
    studies_dir.mkdir(parents=True)
    config_file = studies_dir / "test_study.yaml"
    original_content = "id: test_study\noriginal: true\n"
    config_file.write_text(original_content)

    dae_config = Box({
        "studies": {
            "dir": str(tmp_path / "studies"),
        },
    })
    study_id = "test_study"
    new_config = "id: test_study\nupdated: true\n"

    save_study_config(dae_config, study_id, new_config, force=True)

    # File should contain new config
    assert config_file.read_text() == new_config
    # Backup file should exist
    backup_files = list(studies_dir.glob("test_study.*"))
    assert len(backup_files) == 2  # new config + backup


def test_register_import_storage_factory() -> None:
    def mock_factory() -> Any:
        return "MockStorage"

    register_import_storage_factory("mock_storage", mock_factory)
    storage_types = get_import_storage_types()
    assert "mock_storage" in storage_types


def test_import_project_get_default_bucket_index() -> None:
    assert ImportProject._get_default_bucket_index("denovo") == 0
    assert ImportProject._get_default_bucket_index("vcf") == 100_000
    assert ImportProject._get_default_bucket_index("dae") == 200_000
    assert ImportProject._get_default_bucket_index("cnv") == 300_000
    assert ImportProject._get_default_bucket_index("parquet") == 400_000


def test_import_project_get_processing_region_length_default(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    # Default should be sys.maxsize
    result = project._get_processing_region_length("vcf")
    assert result == sys.maxsize


def test_import_project_get_processing_region_length_custom(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
        "processing_config": {
            "vcf": {
                "region_length": 10_000_000,
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    result = project._get_processing_region_length("vcf")
    assert result == 10_000_000


def test_import_project_get_processing_region_length_string_mode(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
        "processing_config": {
            "vcf": "single_bucket",
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    result = project._get_processing_region_length("vcf")
    assert result is None


def test_import_project_get_loader_target_chromosomes_none(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    result = project._get_loader_target_chromosomes("vcf")
    assert result is None


def test_import_project_get_loader_target_chromosomes_all(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
        "processing_config": {
            "vcf": {
                "chromosomes": ["all"],
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    result = project._get_loader_target_chromosomes("vcf")
    assert result is not None
    assert len(result) > 0
    # Should contain all chromosomes from reference genome


def test_import_project_get_loader_target_chromosomes_specific(
    tmp_path: pathlib.Path,
) -> None:
    gpf = foobar_gpf(tmp_path / "foobar")

    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
        "processing_config": {
            "vcf": {
                "chromosomes": ["foo", "bar"],
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf)

    result = project._get_loader_target_chromosomes("vcf")
    assert result == ["foo", "bar"]


def test_import_project_get_loader_processing_config(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
        "processing_config": {
            "vcf": {
                "region_length": 10_000_000,
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    result = project._get_loader_processing_config("vcf")
    assert result == {"region_length": 10_000_000}


def test_import_project_get_loader_processing_config_empty(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {
            "vcf": {
                "files": ["test.vcf"],
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    result = project._get_loader_processing_config("vcf")
    assert result == {}


def test_import_project_str_representation(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "my_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    assert str(project) == "Project(my_study)"


def test_import_project_pickling_preserves_gpf_instance(
    gpf_fixture: GPFInstance,
) -> None:
    import_config = {
        "id": "test_study",
        "input": {},
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)

    # Get state for pickling
    state = project.__getstate__()
    assert "_gpf_instance" not in state
    assert "_gpf_dae_config" in state
    assert "_gpf_dae_dir" in state

    # Simulate unpickling
    new_project = ImportProject.__new__(ImportProject)
    new_project.__setstate__(state)

    assert new_project._gpf_instance is not None
    assert new_project.get_gpf_instance() is not None


def test_import_config_normalizer_map_for_key() -> None:
    normalizer = ImportConfigNormalizer()
    config = {
        "partition_description": {
            "region_bin": {
                "region_length": "10M",
            },
        },
        "processing_config": {
            "region_length": "5M",
        },
    }

    normalizer._map_for_key(config, "region_length", lambda x: x * 2)

    assert config[
        "partition_description"
    ]["region_bin"]["region_length"] == "10M10M"  # type: ignore
    assert config[
        "processing_config"
    ]["region_length"] == "5M5M"  # type: ignore


def test_import_config_normalizer_normalize_parquet_row_group_size_none(
) -> None:
    normalizer = ImportConfigNormalizer()
    config = {
        "id": "test_study",
        "input": {},
        "processing_config": {
            "parquet_row_group_size": None,
        },
    }

    normalized, _, _ = normalizer.normalize(config, "")

    assert "parquet_row_group_size" not in normalized.get(
        "processing_config", {})


def test_import_config_normalizer_normalize_parquet_row_group_size_value(
) -> None:
    normalizer = ImportConfigNormalizer()
    config = {
        "id": "test_study",
        "input": {},
        "processing_config": {
            "parquet_row_group_size": "100k",
        },
    }

    normalized, _, _ = normalizer.normalize(config, "")

    assert normalized["processing_config"]["parquet_row_group_size"] \
        == 100_000
