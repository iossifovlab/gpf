import pytest


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
def test_summary_stats_simple(
        variants_impl, variants):

    vvars = variants_impl(variants)("backends/summary_stats")
    assert vvars is not None

    vs = vvars.query_variants()
    vs = list(vs)
    print(vs)

    assert len(vs) == 5


@pytest.mark.parametrize("variants", ["variants_impala",])  # "variants_vcf"])
def test_summary_stats_summary(variants_impl, variants):

    vvars = variants_impl(variants)("backends/summary_stats")
    assert vvars is not None

    vs = vvars.query_summary_variants()
    vs = list(vs)
    print(vs)

    assert len(vs) == 1
    count = 0
    for v in vs:
        for aa in v.matched_alleles:
            print(aa, aa.get_attribute("family_variants_count"))
        count += max([
            aa.get_attribute("family_variants_count")
            for aa in v.matched_alleles])
    
    assert count == 5