# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region


@pytest.mark.parametrize("variants", [
    "variants_impala",
    "variants_vcf"
])
def test_summary_stats_simple(
        variants_impl, variants):

    vvars = variants_impl(variants)("backends/summary_stats")
    assert vvars is not None

    vs = vvars.query_variants()
    vs = list(vs)
    print(vs)

    assert len(vs) == 15


@pytest.mark.parametrize("variants", ["variants_impala", ])  # "variants_vcf"])
@pytest.mark.parametrize("regions,inheritance,sv_count,fv_count", [
    ([Region("1", 865581, 865581)], None, 1, 5),
    ([Region("1", 865582, 865582)], None, 2, 5),  # one denovo, one transmitted
    ([Region("1", 865581, 865582)], None, 3, 10),
    ([Region("1", 865582, 865582)], "denovo", 1, 1),
    ([Region("1", 865581, 865582)], "denovo", 1, 1),
    ([Region("1", 865581, 865583)], "denovo", 1, 1),
    ([Region("1", 865583, 865583)], None, 3, 8),  # FIXME: 1, 5
    ([Region("1", 865581, 865583)], None, 6, 18),  # FIXME: 3, 15
])
def test_summary_stats_summary(
        variants_impl, variants, regions, inheritance, sv_count, fv_count):

    vvars = variants_impl(variants)("backends/summary_stats")
    assert vvars is not None

    vs = vvars.query_summary_variants(
        regions=regions,
        inheritance=inheritance)
    vs = list(vs)
    print(vs)

    assert len(vs) == sv_count

    result = 0
    for v in vs:
        for aa in v.matched_alleles:
            print(aa, aa.get_attribute("family_variants_count"))
        result += max([
            aa.get_attribute("family_variants_count")
            for aa in v.matched_alleles])

    assert result == fv_count
