# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import logging

import pytest

from dae.genotype_storage.genotype_storage_registry import \
    GenotypeStorageRegistry, GenotypeStorage

pytest_plugins = ["dae_conftests.dae_conftests"]
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def hdfs_host() -> str:
    return os.environ.get("DAE_HDFS_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_host() -> str:
    return os.environ.get("DAE_IMPALA_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_genotype_storage(
        request: pytest.FixtureRequest,
        hdfs_host: str,
        impala_host: str) -> GenotypeStorage:

    storage_config = {
        "id": "impala_test_storage",
        "storage_type": "impala",
        "impala": {
            "hosts": [impala_host],
            "port": 21050,
            "db": "impala_test_db",
            "pool_size": 5,
        },
        "hdfs": {
            "host": hdfs_host,
            "port": 8020,
            "base_dir": "/tmp/test_data"},
    }
    registry = GenotypeStorageRegistry()
    registry.register_storage_config(storage_config)

    def fin() -> None:
        registry.shutdown()

    request.addfinalizer(fin)

    return registry.get_genotype_storage("impala_test_storage")
