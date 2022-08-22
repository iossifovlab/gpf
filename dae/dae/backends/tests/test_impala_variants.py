# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.variants.variant import SummaryVariant


def test_hdfs_helpers(hdfs_host):
    hdfs = HdfsHelpers(hdfs_host, 8020)

    dirname = hdfs.tempdir()
    print(dirname)
    assert hdfs.exists(dirname)
    assert hdfs.isdir(dirname)


@pytest.mark.parametrize("fixture_name", ["backends/a"])
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

    assert len(vs) == 6


@pytest.mark.parametrize("fixture_name", ["backends/quads_f2"])
def test_impala_summary_variants_simple(variants_impala, fixture_name):
    fvars = variants_impala(fixture_name)

    vs = list(fvars.query_summary_variants())
    print(len(vs))

    for v in vs:
        print(v)
        for a in v.alt_alleles:
            print(">", a)
    for v in vs:
        for a in v.alt_alleles:
            assert a.get_attribute("family_variants_count") == 2
            assert a.get_attribute("seen_in_status") == 3
            assert not a.get_attribute("seen_as_denovo")

    assert all([isinstance(sv, SummaryVariant) for sv in vs])
    assert len(vs) == 2
