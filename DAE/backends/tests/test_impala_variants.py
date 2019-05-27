import pytest
from backends.impala.parquet_io import HdfsHelpers
from backends.impala.impala_backend import ImpalaBackend


def test_hdfs_helpers():
    hdfs = HdfsHelpers()
    assert hdfs is not None

    dirname = hdfs.tempdir()
    print(dirname)


@pytest.mark.parametrize("fixture_name", [
    "fixtures/a",
])
def test_variants_import(test_hdfs, impala_parquet_variants, fixture_name):
    conf = impala_parquet_variants(fixture_name)
    print(conf)

    assert test_hdfs.exists(conf.files.variants)
    assert test_hdfs.exists(conf.files.pedigree)

    backend = ImpalaBackend(
        "dory.seqpipe.org", 21050,
        "dory.seqpipe.org", 8020)
    assert backend is not None

    backend.import_variants(conf)

    ped_df = backend.load_pedigree(conf)
    assert ped_df is not None
    print(ped_df)


@pytest.mark.parametrize("fixture_name", [
    "fixtures/a",
])
def test_variants_db_import(test_impala_backend, impala_variants, fixture_name):
    conf = impala_variants(fixture_name)
    print(conf)

    ped_df = test_impala_backend.load_pedigree(conf)
    assert ped_df is not None
    print(ped_df)


def test_impala_backend_simple():
    hdfs = ImpalaBackend.get_hdfs("dory.seqpipe.org", 8020)
    assert hdfs is not None

    with ImpalaBackend.get_impala("dory.seqpipe.org", 21050) as conn:
        assert conn is not None
