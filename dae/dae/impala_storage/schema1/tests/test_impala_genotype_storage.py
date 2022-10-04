# pylint: disable=W0621,C0114,C0116,W0212,W0613
import re
import os
from contextlib import closing

import pytest
from box import Box  # type: ignore

from dae.impala_storage.schema1.impala_genotype_storage import \
    ImpalaGenotypeStorage


@pytest.fixture(scope="session")
def impala_genotype_storage():
    storage_config = Box({
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
    })
    return ImpalaGenotypeStorage(storage_config)


def test_storage_type(impala_genotype_storage):
    assert impala_genotype_storage.get_storage_type() == "impala"


def test_impala_helpers(impala_genotype_storage):
    impala_helpers = impala_genotype_storage.impala_helpers

    assert impala_helpers is not None
    assert impala_helpers.connection is not None


def test_impala_partition_import(
        impala_genotype_storage, fixture_dirname):

    ped_file = fixture_dirname(
        "backends/test_partition2/pedigree/pedigree.parquet")
    variants_path = fixture_dirname(
        "backends/test_partition2/variants")

    impala_genotype_storage.impala_load_dataset(
        "test_study", variants_path, ped_file)

    hdfs = impala_genotype_storage.hdfs_helpers
    root = impala_genotype_storage.storage_config.hdfs.base_dir

    assert hdfs.exists(
        os.path.join(
            root,
            "test_study/variants/region_bin=1_8/frequency_bin=3/"
            "coding_bin=0/family_bin=6/",
        )
    )
    assert hdfs.exists(
        os.path.join(
            root,
            "test_study/variants/region_bin=1_8/frequency_bin=3/coding_bin=0/"
            "/family_bin=6/"
            "variants_region_bin_1_8_frequency_bin_3_"
            "coding_bin_0_family_bin_6.parquet",
        )
    )
    assert hdfs.exists(
        os.path.join(
            root,
            "test_study/variants/region_bin=1_8/frequency_bin=3"
            "/coding_bin=0/family_bin=69",
        )
    )
    assert hdfs.exists(
        os.path.join(
            root,
            "test_study/variants/region_bin=1_8/frequency_bin=3/coding_bin=0/"
            "/family_bin=69/"
            "variants_region_bin_1_8_frequency_bin_3_"
            "coding_bin_0_family_bin_69.parquet",
        )
    )
    # assert hdfs.exists(
    #     os.path.join(
    #         root,
    #         "test_study/variants/region_bin=2_9/family_bin=6/coding_bin=0/"
    #         "frequency_bin=3",
    #     )
    # )
    # assert hdfs.exists(
    #     os.path.join(
    #         root,
    #         "test_study/variants/region_bin=2_9/family_bin=6/coding_bin=0/"
    #         "frequency_bin=3/"
    #         "variants_region_bin_2_9_family_bin_6_"
    #         "coding_bin_0_frequency_bin_3.parquet",
    #     )
    # )
    # assert hdfs.exists(
    #     os.path.join(
    #         root,
    #         "test_study/variants/region_bin=2_9/family_bin=69"
    #         "/coding_bin=0/frequency_bin=3",
    #     )
    # )
    # assert hdfs.exists(
    #     os.path.join(
    #         root,
    #         "test_study/variants/region_bin=2_9/family_bin=69/coding_bin=0/"
    #         "frequency_bin=3/"
    #         "variants_region_bin_2_9_family_bin_69_"
    #         "coding_bin_0_frequency_bin_3.parquet",
    #     )
    # )

    impala_helpers = impala_genotype_storage.impala_helpers
    db = impala_genotype_storage.storage_config.impala.db

    with closing(impala_helpers.connection()) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"DESCRIBE EXTENDED {db}.test_study_variants")
            rows = list(cursor)
            assert any(
                row[1] == "gpf_partitioning_coding_bin_coding_effect_types"
                and row[2] == "missense,nonsense,frame-shift,synonymous"
                for row in rows
            )
            assert any(
                row[1] == "gpf_partitioning_family_bin_family_bin_size"
                and int(row[2]) == 100
                for row in rows
            )
            assert any(
                row[1] == "gpf_partitioning_frequency_bin_rare_boundary"
                and int(row[2]) == 30
                for row in rows
            )
            assert any(
                row[1] == "gpf_partitioning_region_bin_chromosomes"
                and "1, 2" in row[2]
                for row in rows
            )
            assert any(
                row[1] == "gpf_partitioning_region_bin_region_length"
                and int(row[2]) == 100000
                for row in rows
            )


def test_impala_genotype_storate_has_rsync_helpers(mocker):
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "impala": {
            "db": "test",
            "hosts": ["localhost"],
            "port": 21050,
            "pool_size": 3,
        },
        "hdfs": {
            "base_dir": "/tmp/genotype_impala",
            "host": "locahost",
            "port": 8020,
        },
        "rsync": {
            "location": "ssh://dory:/mnt/hdfs2mnt",
        },
    }

    storage = ImpalaGenotypeStorage(config)
    assert storage is not None
    assert storage.rsync_helpers is not None


def test_impala_genotype_storate_no_rsync_helpers(mocker):
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "impala": {
            "db": "test",
            "hosts": ["localhost"],
            "port": 21050,
            "pool_size": 3,
        },
        "hdfs": {
            "base_dir": "/tmp/genotype_impala",
            "host": "locahost",
            "port": 8020,
        },
        "rsync": None,
    }
    storage = ImpalaGenotypeStorage(config)
    assert storage is not None
    assert storage.rsync_helpers is None


def test_create_impala_genotype_storage():
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
    res = ImpalaGenotypeStorage(config)
    assert res is not None


def test_create_impala_genotype_storage_missing_id():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_type():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_wrong_type():
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
                "storage configuration for <impala2> passed to genotype "
                "storage class type <impala>")):
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_hdfs():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_hdfs_base_dir():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_bad_hdfs_path():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_hdfs_host():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_hdfs_port():
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
    res = ImpalaGenotypeStorage(config)
    assert res.storage_config["hdfs"]["port"] == 8020


def test_create_impala_genotype_storage_missing_hdfs_replication():
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
    res = ImpalaGenotypeStorage(config)
    assert res.storage_config["hdfs"]["replication"] == 1


def test_create_impala_genotype_storage_missing_impala():
    config = {
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        # "impala": {
        #     "db": "impala_storage_test_db",
        #     "hosts": [
        #         "localhost",
        #     ],
        #     "pool_size": 3,
        #     "port": 21050,
        # },
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for impala storage: "
                "{'impala': ['required field']}")):
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_impala_db():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_impala_hosts():
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
        ImpalaGenotypeStorage(config)


def test_create_impala_genotype_storage_missing_impala_port():
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
    res = ImpalaGenotypeStorage(config)
    assert res.storage_config["impala"]["port"] == 21050


def test_create_impala_genotype_storage_missing_impala_pool_size():
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
    res = ImpalaGenotypeStorage(config)
    assert res.storage_config["impala"]["pool_size"] == 1
