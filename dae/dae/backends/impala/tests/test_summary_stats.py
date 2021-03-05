import pytest

from dae.utils.regions import Region


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
def test_summary_stats_simple(
        variants_impl, variants):

    vvars = variants_impl(variants)("backends/summary_stats")
    assert vvars is not None

    vs = vvars.query_variants()
    vs = list(vs)
    print(vs)

    assert len(vs) == 10


@pytest.mark.parametrize("variants", ["variants_impala", ])  # "variants_vcf"])
@pytest.mark.parametrize("regions,inheritance,count", [
    ([Region("1", 865581, 865581)], None, 5),
    ([Region("1", 865582, 865582)], None, 5),
    ([Region("1", 865581, 865582)], None, 10),
    ([Region("1", 865582, 865582)], "denovo", 1),
    ([Region("1", 865581, 865582)], "denovo", 1),
])
def test_summary_stats_summary(
        variants_impl, variants, regions, inheritance, count):

    vvars = variants_impl(variants)("backends/summary_stats")
    assert vvars is not None

    vs = vvars.query_summary_variants(
        regions=regions,
        inheritance=inheritance)
    vs = list(vs)
    print(vs)

    # assert len(vs) == 1
    result = 0
    for v in vs:
        for aa in v.alt_alleles:
            print(aa, aa.get_attribute("family_variants_count"))
        result += max([
            aa.get_attribute("family_variants_count")
            for aa in v.matched_alleles])

    assert result == count
