# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import os
import pathlib
from collections.abc import Generator

import pytest

from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorage,
    GenotypeStorageRegistry,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def resources_dir(request: pytest.FixtureRequest) -> pathlib.Path:
    resources_path = os.path.join(
        os.path.dirname(os.path.realpath(request.module.__file__)),
        "resources")
    return pathlib.Path(resources_path)


@pytest.fixture(scope="session")
def hdfs_host() -> str:
    return os.environ.get("DAE_HDFS_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_host() -> str:
    return os.environ.get("DAE_IMPALA_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_genotype_storage(
        hdfs_host: str,
        impala_host: str) -> Generator[GenotypeStorage, None, None]:

    storage_config = {
        "id": "impala2_test_storage",
        "storage_type": "impala2",
        "impala": {
            "hosts": [impala_host],
            "port": 21050,
            "db": "impala_test_db",
            "pool_size": 5,
        },
        "hdfs": {
            "host": hdfs_host,
            "port": 8020,
            "base_dir": "/tmp/test_data",  # noqa: S108
        },
    }
    registry = GenotypeStorageRegistry()
    registry.register_storage_config(storage_config)

    yield registry.get_genotype_storage("impala2_test_storage")

    registry.shutdown()
