# pylint: disable=W0621,C0114,C0116,W0212,W0613
import re
import pytest

from impala_storage.schema1.impala_genotype_storage import \
    ImpalaGenotypeStorage


def test_impala_config_validation():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    res = ImpalaGenotypeStorage.validate_and_normalize_config(config)
    assert res is not None


def test_impala_config_validation_missing_id():
    config = {
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without ID; 'id' is required"):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_type():
    config = {
        "id": "aaaa",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without type; 'storage_type' is required"):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_wrong_type():
    config = {
        "id": "aaaa",
        "storage_type": "impala2",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "storage configuration for <impala2> passed to "
                "genotype storage class type <impala>")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_hdfs():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        # "hdfs": {
        #     "base_dir": "/tmp/test_data",
        #     "host": "localhost",
        #     "port": 8020,
        #     "replication": 1,
        # },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'hdfs': ['required field']}")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_hdfs_base_dir():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            # "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'hdfs': [{'base_dir': ['required field']}]}")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_bad_hdfs_path():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'hdfs': [{'base_dir': "
                "['path <tmp/test_data> is not an absolute path']}]}")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_hdfs_host():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            # "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'hdfs': [{'host': ['required field']}]}")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_hdfs_port():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            # "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    res = ImpalaGenotypeStorage.validate_and_normalize_config(config)
    assert res["hdfs"]["port"] == 8020


def test_impala_config_validation_missing_hdfs_replication():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            # "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    res = ImpalaGenotypeStorage.validate_and_normalize_config(config)
    assert res["hdfs"]["replication"] == 1


def test_impala_config_validation_missing_impala():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'impala': ['required field']}")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_impala_db():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            # "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'impala': [{'db': ['required field']}]}")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_impala_hosts():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            # "hosts": [
            #     "localhost",
            # ],
            "pool_size": 3,
            "port": 21050,
        },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'impala': [{'hosts': ['required field']}]}")):
        ImpalaGenotypeStorage.validate_and_normalize_config(config)


def test_impala_config_validation_missing_impala_port():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            # "port": 21050,
        },
    }
    res = ImpalaGenotypeStorage.validate_and_normalize_config(config)
    assert res["impala"]["port"] == 21050


def test_impala_config_validation_missing_impala_pool_size():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "port": 21050,
            # "pool_size": 3,
        },
    }
    res = ImpalaGenotypeStorage.validate_and_normalize_config(config)
    assert res["impala"]["pool_size"] == 1
