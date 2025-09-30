# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from typing import Any

import pytest
import yaml
from dae.testing.acgt_import import acgt_gpf
from dae.testing.import_helpers import (
    StudyInputLayout,
    setup_import_project_config,
)


@pytest.mark.parametrize("config_update, key, subkeys", [
    ({}, "processing_config", {"work_dir"}),
    ({"partition_description": {
        "region_bin": {
            "region_length": 22,
        },
    }}, "partition_description", {"region_bin"}),
    ({"processing_config": {
        "parquet_dataset_dir": "aaa",
    }}, "processing_config", {"work_dir", "parquet_dataset_dir"}),
])
def test_setup_import_project(
    tmp_path_factory: pytest.TempPathFactory,
    config_update: dict[str, Any],
    key: str,
    subkeys: set[str],
) -> None:
    root_path = tmp_path_factory.mktemp("test_import_project")
    gpf_instance = acgt_gpf(root_path)
    study = StudyInputLayout(
        "test_id", root_path / "fam.ped", [root_path / "in.vcf"], [], [], [])

    pathname = setup_import_project_config(
        root_path, study, gpf_instance, config_update)

    project_config = yaml.safe_load(pathname.read_text())
    assert set(project_config[key]) == subkeys
