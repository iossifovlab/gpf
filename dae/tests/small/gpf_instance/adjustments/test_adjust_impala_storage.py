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
                    "id": "genotype_impala",
                    "storage_type": "impala",
                    "read_only": True,
                    "hdfs": {
                        "base_dir": "/user/data_hg38_local/studies",
                        "host": "hdfs",
                        "port": "8020",
                    },
                    "impala": {
                        "db": "data_hg38_local",
                        "hosts": [
                            "impala1",
                            "impala2",
                        ],
                        "port": "21050",
                        "pool_size": "3",
                    },
                },
            ],
        },
    }
    config_file = tmp_path / "gpf_instance.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file


def test_gpf_instance_adjust_impala_storage(
    gpf_instance_config: pathlib.Path,
) -> None:
    """Test adjustment of impala storage base_dir."""

    cli([
        "-i", str(gpf_instance_config.parent),
        "impala-storage",
        "--storage-id", "genotype_impala",
        "--hdfs-host", "localhost",
        "--impala-hosts", "localhost",
        "--no-read-only",
    ])

    with open(gpf_instance_config, "r") as f:
        config = yaml.safe_load(f)
    storages = config["genotype_storage"]["storages"]
    assert storages[0]["impala"]["db"] == "data_hg38_local"
    assert storages[0]["hdfs"]["base_dir"] == "/user/data_hg38_local/studies"
    assert storages[0]["hdfs"]["host"] == "localhost"
    assert storages[0]["impala"]["hosts"] == ["localhost"]
