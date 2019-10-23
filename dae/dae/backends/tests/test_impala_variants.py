import pytest
from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers


def test_hdfs_helpers():
    hdfs = HdfsHelpers.get_hdfs()
    assert hdfs is not None

    dirname = hdfs.tempdir()
    print(dirname)


def test_impala_connection_simple():

    with ImpalaHelpers.get_impala('127.0.0.1', 21050) as conn:
        assert conn is not None


@pytest.mark.parametrize("fixture_name", [
    "backends/a",
])
def test_impala_variants_simple(variants_impala, fixture_name):
    fvars = variants_impala(fixture_name)

    vs = list(fvars.query_variants())
    print(len(vs))

    for v in vs:
        print(v)
        for a in v.alt_alleles:
            print(">", a)
        for a in v.matched_alleles:
            print(">", a)

    assert len(vs) == 5
