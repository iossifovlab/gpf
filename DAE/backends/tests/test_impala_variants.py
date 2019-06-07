import pytest
from backends.impala.parquet_io import HdfsHelpers
from backends.impala.impala_backend import ImpalaBackend


def test_hdfs_helpers():
    hdfs = HdfsHelpers()
    assert hdfs is not None

    dirname = hdfs.tempdir()
    print(dirname)


def test_impala_backend_simple():
    hdfs = ImpalaBackend.get_hdfs()
    assert hdfs is not None

    with ImpalaBackend.get_impala() as conn:
        assert conn is not None


# @pytest.mark.parametrize("fixture_name", [
#     "backends/a",
# ])
# def test_variants_import(test_hdfs, impala_parquet_variants, fixture_name):
#     conf = impala_parquet_variants(fixture_name)
#     print(conf)

#     assert test_hdfs.exists(conf.files.variant)
#     assert test_hdfs.exists(conf.files.pedigree)

#     backend = ImpalaBackend()
#     assert backend is not None

#     backend.import_variants(conf)

#     ped_df = backend.load_pedigree(conf)
#     assert ped_df is not None
#     print(ped_df)

#     # df = backend.variants_schema(conf)
#     # print(df)


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
