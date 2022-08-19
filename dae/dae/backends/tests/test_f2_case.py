# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.utils.regions import Region


def count_variants(
    variants,
    regions,
    inheritance,
    reference,
    unknown,
    fixture_name="backends/f1_test",
):
    vvars = variants(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        return_reference=reference,
        return_unknown=unknown,
    )
    vs = list(vs)
    for v in vs:
        for a in v.alleles:
            print(a, a.inheritance_in_members, a.variant_in_members)
    return len(vs)


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,reference, unknown, count",
    [
        ([Region("1", 901923, 901923)], None, True, True, 1),
        (
            [Region("1", 901923, 901923)],
            "denovo",
            False,
            False,
            0,
        ),  # find denovo
        (
            [Region("1", 901923, 901923)],
            "not denovo and not omission",
            False,
            False,
            0,
        ),
        ([Region("1", 901923, 901923)], None, True, True, 1),
        ([Region("1", 901923, 901923)], "omission", False, False, 0),
    ],
)
def test_f2_all_unknown(
    variants_impl, variants, regions, inheritance, reference, unknown, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, reference, unknown
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,reference, unknown, count",
    [
        ([Region("1", 905951, 905951)], None, True, True, 1),
        (
            [Region("1", 905951, 905951)],
            "denovo",
            False,
            False,
            0,
        ),  # find denovo
        (
            [Region("1", 905951, 905951)],
            "not denovo and not omission",
            False,
            False,
            0,
        ),
        ([Region("1", 905951, 905951)], None, True, True, 1),  # find all
        (
            [Region("1", 905951, 905951)],
            "omission",
            False,
            False,
            0,
        ),  # find omission
    ],
)
def test_f2_reference_and_unknown(
    variants_impl, variants, regions, inheritance, reference, unknown, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, reference, unknown
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,reference, unknown, count",
    [
        ([Region("1", 905957, 905957)], None, True, True, 1),
        (
            [Region("1", 905957, 905957)],
            "denovo",
            False,
            False,
            1,
        ),  # find denovo
        (
            [Region("1", 905957, 905957)],
            "not denovo and not omission and not unknown and not missing",
            False,
            False,
            0,
        ),
        ([Region("1", 905957, 905957)], None, True, True, 1),  # find all
        (
            [Region("1", 905957, 905957)],
            "omission",
            False,
            False,
            0,
        ),  # find omission
    ],
)
def test_f2_canonical_denovo(
    variants_impl, variants, regions, inheritance, reference, unknown, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, reference, unknown
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,reference, unknown, count",
    [
        ([Region("1", 905966, 905966)], None, True, True, 1),
        (
            [Region("1", 905966, 905966)],
            "denovo",
            False,
            False,
            0,
        ),  # find denovo
        (
            [Region("1", 905966, 905966)],
            "not denovo and not omission and not unknown and not mendelian",
            False,
            False,
            0,
        ),
        ([Region("1", 905966, 905966)], None, True, True, 1),  # find all
        (
            [Region("1", 905966, 905966)],
            "omission",
            False,
            False,
            1,
        ),  # find omission
    ],
)
def test_f2_canonical_omission(
    variants_impl, variants, regions, inheritance, reference, unknown, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, reference, unknown
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,reference, unknown, count",
    [
        ([Region("1", 906092, 906092)], None, True, True, 1),
        (
            [Region("1", 906092, 906092)],
            "denovo",
            False,
            False,
            0,
        ),  # find denovo
        (
            [Region("1", 906092, 906092)],
            "not denovo and not omission and not unknown and not mendelian",
            False,
            False,
            0,
        ),
        ([Region("1", 906092, 906092)], None, True, True, 1),  # find all
        (
            [Region("1", 906092, 906092)],
            "omission",
            False,
            False,
            1,
        ),  # find omission
    ],
)
def test_f2_non_canonical_omission(
    variants_impl, variants, regions, inheritance, reference, unknown, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, reference, unknown
    )
    assert c == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "regions,inheritance,reference, unknown, count",
    [
        ([Region("1", 906086, 906086)], None, True, True, 1),
        (
            [Region("1", 906086, 906086)],
            "denovo",
            False,
            False,
            1,
        ),  # find denovo
        (
            [Region("1", 906086, 906086)],
            "not denovo or not omission",
            False,
            False,
            1,
        ),
        ([Region("1", 906086, 906086)], None, True, True, 1),  # find all
        (
            [Region("1", 906086, 906086)],
            "omission",
            False,
            False,
            0,
        ),  # find omission
    ],
)
def test_f2_partially_unknown_denovo(
    variants_impl, variants, regions, inheritance, reference, unknown, count
):

    c = count_variants(
        variants_impl(variants), regions, inheritance, reference, unknown
    )
    assert c == count
