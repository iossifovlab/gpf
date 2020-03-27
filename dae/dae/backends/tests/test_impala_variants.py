import pytest
from dae.backends.impala.impala_variants import ImpalaFamilyVariants
from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.utils.regions import Region


def test_hdfs_helpers(hdfs_host):
    hdfs = HdfsHelpers(hdfs_host, 8020)
    assert hdfs is not None

    dirname = hdfs.tempdir()
    print(dirname)


def test_impala_query_build(impala_host, genomes_db_2013):
    connection = ImpalaHelpers.create_impala_connection(impala_host, 21050)
    ifv = ImpalaFamilyVariants(
        connection,
        "impala_storage_test_db",
        "test_study_variants",
        "test_study_pedigree",
        genomes_db_2013.get_gene_models(),
    )
    regions = [Region("1", 1, 199999), Region("2", 1, 199999)]
    families = ["f1", "f2"]
    coding_effects = ["missense", "frame-shift"]
    real_attr_filter = [("af_allele_freq", (1, 50))]

    q = ifv.build_query(regions=regions)
    print(q)
    q = ifv.build_query(family_ids=families)
    print(q)
    q = ifv.build_query(effect_types=coding_effects)
    print(q)
    q = ifv.build_query(real_attr_filter=real_attr_filter)
    print(q)
    q = ifv.build_query(
        regions=regions,
        family_ids=families,
        effect_types=coding_effects,
        real_attr_filter=real_attr_filter,
    )
    print(q)


@pytest.mark.parametrize("fixture_name", ["backends/a",])
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
