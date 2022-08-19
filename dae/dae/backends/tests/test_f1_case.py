# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


def test_f1_check_all_variants_effects(variants_vcf):
    vvars = variants_vcf("backends/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(return_reference=True, return_unknown=True)
    vs = list(vs)
    for v in vs:
        print(v, v.effects, mat2str(v.best_state))
        summary_alleles = v.summary_alleles
        sa1 = summary_alleles[1]
        sa2 = summary_alleles[2]

        assert sa1.effects.worst == "synonymous"
        assert sa2.effects.worst == "missense"

    assert len(vs) == 7


def count_variants(variants, regions, inheritance, effect_types):
    vvars = variants("backends/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types,
        return_reference=True,
        return_unknown=True,
    )
    vs = list(vs)
    for v in vs:
        for a in v.alleles:
            print(a, a.inheritance_in_members, a.variant_in_members, a.effects)
    return len(vs)


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 878152, 878152)], None, None, 1),
        ([Region("1", 878152, 878152)], "denovo", ["synonymous"], 0),
        ([Region("1", 878152, 878152)], "denovo", ["missense"], 1),
        ([Region("1", 878152, 878152)], "mendelian", ["synonymous"], 1),
        ([Region("1", 878152, 878152)], "mendelian", ["missense"], 0),
    ],
)
def test_f1_simple(
        variants_impl, variants, regions, inheritance, effect_types, count):

    vvars = variants_impl(variants)("backends/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types,
        return_reference=True,
        return_unknown=True,
    )
    vs = list(vs)
    print(vs)

    assert len(vs) == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 901923, 901923)], None, None, 1),
        ([Region("1", 901923, 901923)], "unknown", None, 1),
        ([Region("1", 901923, 901923)], "mendelian", None, 0),
        ([Region("1", 901923, 901923)], "not unknown", None, 0),
        ([Region("1", 901923, 901923)], None, ["synonymous", "missense"], 0),
    ],
)
def test_f1_all_unknown(
    variants_impl, variants, regions, inheritance, effect_types, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, effect_types
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 905951, 905951)], None, None, 1),
        ([Region("1", 905951, 905951)], "unknown", None, 1),
        ([Region("1", 905951, 905951)], "mendelian", None, 1),
        ([Region("1", 905951, 905951)], "mendelian", ["synonymous"], 0),
        ([Region("1", 905951, 905951)], "mendelian", ["missense"], 0),
        ([Region("1", 905951, 905951)], "not denovo", None, 1),
        ([Region("1", 905951, 905951)], "not omission", None, 1),
        ([Region("1", 905951, 905951)], "not denovo or not omission", None, 1),
    ],
)
def test_f1_unknown_and_reference(
    variants_impl, variants, regions, inheritance, effect_types, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, effect_types
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 905957, 905957)], None, None, 1),
        ([Region("1", 905957, 905957)], "unknown", None, 1),
        ([Region("1", 905957, 905957)], "mendelian", None, 1),
        ([Region("1", 905957, 905957)], "mendelian", ["synonymous"], 0),
        ([Region("1", 905957, 905957)], "mendelian", ["missense"], 0),
        ([Region("1", 905957, 905957)], None, ["synonymous"], 1),
        ([Region("1", 905957, 905957)], None, ["missense"], 0),
        ([Region("1", 905957, 905957)], None, ["synonymous"], 1),
        ([Region("1", 905957, 905957)], "not denovo ", None, 1),
    ],
)
def test_f1_cannonical_denovo(
    variants_impl, variants, regions, inheritance, effect_types, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, effect_types
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 905966, 905966)], None, None, 1),
        ([Region("1", 905966, 905966)], "omission", None, 1),
        ([Region("1", 905966, 905966)], "denovo", None, 0),
        ([Region("1", 905966, 905966)], None, ["synonymous"], 1),
        ([Region("1", 905966, 905966)], None, ["missense"], 0),
        ([Region("1", 905966, 905966)], "omission", ["missense"], 0),
        ([Region("1", 905966, 905966)], "omission", ["synonymous"], 1),
        ([Region("1", 905966, 905966)], "mendelian", None, 1),
    ],
)
def test_f1_cannonical_omission(
    variants_impl, variants, regions, inheritance, effect_types, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, effect_types
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 906092, 906092)], None, None, 1),
        ([Region("1", 906092, 906092)], "omission", None, 1),
        ([Region("1", 906092, 906092)], "denovo", None, 0),
        ([Region("1", 906092, 906092)], "omission", ["synonymous"], 1),
        ([Region("1", 906092, 906092)], "omission", ["missense"], 1),
        (
            [Region("1", 906092, 906092)],
            "not omission and not mendelian and not unknown",
            ["missense"],
            0,
        ),
        ([Region("1", 906092, 906092)], "not omission", None, 1),
        ([Region("1", 906092, 906092)], "not mendelian", None, 1),
    ],
)
def test_f1_non_cannonical_omission(
    variants_impl, variants, regions, inheritance, effect_types, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, effect_types
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 906086, 906086)], None, None, 1),
        ([Region("1", 906086, 906086)], "denovo", None, 1),
        ([Region("1", 906086, 906086)], "denovo", ["synonymous"], 0),
        ([Region("1", 906086, 906086)], "denovo", ["missense"], 1),
        ([Region("1", 906086, 906086)], "mendelian", None, 1),
    ],
)
def test_f1_partially_known_denovo(
    variants_impl, variants, regions, inheritance, effect_types, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, effect_types
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("1", 901923, 901923)], None, None, 1),
        ([Region("1", 901923, 901923)], "unknown", None, 1),
        ([Region("1", 901923, 901923)], "mendelian", None, 0),
        ([Region("1", 901923, 901923)], "not unknown", None, 0),
        ([Region("1", 901923, 901923)], None, ["synonymous", "missense"], 0),
    ],
)
def test_f1_all_unknown_901923(
    variants_impl, variants, regions, inheritance, effect_types, count
):

    vvars = variants_impl(variants)("backends/f1_test_901923")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types,
        return_reference=True,
        return_unknown=True,
    )

    vs = list(vs)
    assert len(vs) == count
