# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Type

import cloudpickle
import pytest

from impala2_storage.schema2.impala2_genotype_storage import (
    Impala2GenotypeStorage,
)


@pytest.mark.parametrize("storage_cls, storage_type", [
    (Impala2GenotypeStorage, "impala2"),
])
def test_genotype_storage_is_cpickle_serializable(
    storage_cls: Type[Impala2GenotypeStorage],
    storage_type: str,
) -> None:
    storage = storage_cls({
        "id": "storage",
        "storage_type": storage_type,
        "impala": {
            "db": "db_name",
            "hosts": ["localhost"],
            "port": 21050,
            "pool_size": 3,
        },
        "hdfs": {
            "base_dir": "/studies",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
    })
    _ = cloudpickle.dumps(storage)
