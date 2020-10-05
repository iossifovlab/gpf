import pytest
from dae.backends.impala.impala_variants import ImpalaFamilyVariants
from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.variants.variant import SummaryVariant
from dae.utils.regions import Region


def test_hdfs_helpers(hdfs_host):
    hdfs = HdfsHelpers(hdfs_host, 8020)
    assert hdfs is not None

    dirname = hdfs.tempdir()
    print(dirname)


def test_impala_query_build(impala_host, genomes_db_2013):
    impala_helpers = ImpalaHelpers([impala_host], 21050)
    ifv = ImpalaFamilyVariants(
        impala_helpers,
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

    assert len(vs) == 5


@pytest.mark.parametrize("fixture_name", ["backends/a"])
def test_impala_summary_variants_simple(variants_impala, fixture_name):
    fvars = variants_impala(fixture_name)

    vs = list(fvars.query_summary_variants())
    print(len(vs))

    for v in vs:
        print(v)
        for a in v.alt_alleles:
            print(">", a)

    assert all([isinstance(sv, SummaryVariant) for sv in vs])
    assert len(vs) == 5


@pytest.mark.parametrize("inheritance,ultra_rare,real_attr_filter, result", [
    (
        "denovo", None, None,
        "frequency_bin = 0"
    ),
    (
        None, None, None,
        ""
    ),
    (
        "any(denovo, mendelian)", None, None,
        ""
    ),
    (
        "any(denovo)", True, None,
        "frequency_bin = 0"
    ),
    (
        "any(denovo, mendelian)", True, None,
        " OR ".join(set(["frequency_bin = 0", "frequency_bin = 1"]))
    ),
    (
        None, True, None,
        " OR ".join(set(["frequency_bin = 1"]))
    ),
    (
        "any(mendelian)", True, None,
        " OR ".join(set(["frequency_bin = 1"]))
    ),
    (
        "any(mendelian)", None, [("af_allele_freq", (0, 3))],
        " OR ".join(set(["frequency_bin = 1", "frequency_bin = 2"]))
    ),
    (
        "any(denovo, mendelian)", None, [("af_allele_freq", (0, 3))],
        " OR ".join(set([
            "frequency_bin = 0", "frequency_bin = 1",
            "frequency_bin = 2"]))
    ),
    (
        "any(denovo, mendelian)", None, [("af_allele_freq", (0, 5))],
        " OR ".join(set([]))
    ),
    (
        "any(denovo, mendelian)", None, [("af_allele_freq", (5, 6))],
        " OR ".join(set([
            "frequency_bin = 0", "frequency_bin = 3"]))
    ),
    (
        None, None, [("af_allele_freq", (0, 3))],
        " OR ".join(set([
            "frequency_bin = 1",
            "frequency_bin = 2"]))
    ),
])
def test_impala_frequency_bin_heuristics(
        mocker, impala_helpers, genomes_db_2013,
        inheritance, ultra_rare, real_attr_filter, result):

    ifv = ImpalaFamilyVariants(
        impala_helpers,
        "impala_storage_test_db",
        "test_study_variants",
        "test_study_pedigree",
        genomes_db_2013.get_gene_models(),
    )
    ifv.rare_boundary = 5

    q = ifv._build_frequency_bin_heuristic(
        inheritance, ultra_rare, real_attr_filter)

    assert result == q
