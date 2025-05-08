# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
import yaml

from dae.gpf_instance.adjustments.gpf_instance_adjustments import (
    cli,
)


@pytest.fixture
def gpf_instance_config(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for GPF instance config."""
    config = {
        "instance_id": "test_gpf_instance_fixture",
        "reference_genome": {
            "resource_id": "hg38/genomes/GRCh38-hg38",
        },
        "gene_models": {
            "resource_id": "hg38/gene_models/refGene_v20170601",
        },
        "genotype_storage": {
            "storages": [
                {
                    "id": "duckdb",
                    "storage_type": "duckdb",
                    "db": "duckdb.db",
                    "base_dir": str(tmp_path / "duckdb_storage"),
                },
                {
                    "id": "duckdb_parquet",
                    "storage_type": "duckdb_parquet",
                    "base_dir": str(tmp_path / "duckdb_storage" / "parquet"),
                    "memory_limit": "12GB",
                },
            ],
        },
    }
    config_file = tmp_path / "gpf_instance.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file


def test_gpf_instance_adjust_duckdb_parquet(
    gpf_instance_config: pathlib.Path,
) -> None:
    """Test adjustment of duckdb storage base_dir."""

    cli([
        "-i", str(gpf_instance_config.parent),
        "duckdb-storage",
        "--storage-id", "duckdb_parquet",
        "--base-dir", "/aaa/duckdb_storage",
    ])

    with open(gpf_instance_config, "r") as f:
        config = yaml.safe_load(f)
    storages = config["genotype_storage"]["storages"]

    assert storages[1]["base_dir"] == "/aaa/duckdb_storage"


def test_gpf_instance_adjust_duckdb(
    gpf_instance_config: pathlib.Path,
) -> None:
    """Test adjustment of duckdb storage base_dir."""

    cli([
        "-i", str(gpf_instance_config.parent),
        "duckdb-storage",
        "--storage-id", "duckdb",
        "--base-dir", "/aaa/duckdb_storage",
        "--db", "aaaaa.db",
    ])

    with open(gpf_instance_config, "r") as f:
        config = yaml.safe_load(f)
    storages = config["genotype_storage"]["storages"]

    assert storages[0]["base_dir"] == "/aaa/duckdb_storage"
    assert storages[0]["db"] == "aaaaa.db"
