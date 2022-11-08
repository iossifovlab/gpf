# pylint: disable=W0621,C0114,C0116,W0212,W0613
import cloudpickle  # type: ignore
import pytest
from dae.impala_storage.schema1.impala_genotype_storage import \
    ImpalaGenotypeStorage
from dae.impala_storage.schema2.schema2_genotype_storage import \
    Schema2GenotypeStorage


@pytest.mark.parametrize("storage_cls, storage_type", [
    (ImpalaGenotypeStorage, "impala"),
    (Schema2GenotypeStorage, "impala2"),
])
def test_genotype_storage_is_cpickle_serializable(storage_cls, storage_type):
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
        }
    })
    _ = cloudpickle.dumps(storage)
