# pylint: disable=C0114,C0116,W0621
from io import StringIO
from typing import Any

import numpy as np
import pytest

from gpf.inmemory_storage.raw_variants import RawFamilyVariants
from gpf.pedigrees.family import Family
from gpf.pedigrees.loader import FamiliesLoader
from gpf.utils.variant_utils import GenotypeType
from gpf.variants.attributes import Inheritance, Role, Sex, Status
from gpf.variants.core import Allele
from gpf.variants.family_variant import FamilyAllele
from gpf.variants.variant import SummaryAllele

# Members in column order: d1 (dad), m1 (mom), p1 (prb).
PED1 = """
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
"""

# p1 carries a de novo alt allele, the parents are reference.
DENOVO_IN_PRB = np.array([[0, 0, 0], [0, 0, 1]], dtype=GenotypeType)
# m1 is heterozygous, p1 is homozygous for the alt allele.
HET_MOM_HOM_PRB = np.array([[0, 0, 1], [0, 1, 1]], dtype=GenotypeType)
# Nobody carries the alt allele.
ALL_REFERENCE = np.array([[0, 0, 0], [0, 0, 0]], dtype=GenotypeType)

EFFECT_G1_MISSENSE = "missense!g1:missense!tx1:g1:missense:p.X"


class RecordingMatcher:
    """A matcher that records its arguments and returns a fixed result."""

    def __init__(self, *, result: bool = True) -> None:
        self.result = result
        self.calls: list[tuple[int, int | None]] = []

    def __call__(self, a: int, b: int | None = None) -> bool:
        self.calls.append((a, b))
        return self.result


@pytest.fixture
def trio() -> Family:
    families = FamiliesLoader(StringIO(PED1), ped_sep=",").load()
    return families["f1"]


def make_allele(
    family: Family,
    genotype: np.ndarray = DENOVO_IN_PRB, *,
    allele_index: int = 1,
    attributes: dict[str, Any] | None = None,
    effect: str | None = None,
) -> FamilyAllele:
    summary_allele = SummaryAllele(
        "chr1", 10, "A", "T" if allele_index else None,
        summary_index=0, allele_index=allele_index,
        attributes=attributes, effect=effect,
    )
    return FamilyAllele(
        summary_allele, family, genotype=genotype, best_state=None)


def make_reference_allele(family: Family) -> FamilyAllele:
    return make_allele(family, allele_index=0)


# allele

def test_summary_allele_is_rejected_with_an_assertion() -> None:
    summary_allele = SummaryAllele("chr1", 10, "A", "T", allele_index=1)

    with pytest.raises(AssertionError):
        RawFamilyVariants.filter_allele(
            summary_allele)  # type: ignore[arg-type]


def test_alt_allele_passes_with_default_arguments(trio: Family) -> None:
    allele = make_allele(trio)

    assert RawFamilyVariants.filter_allele(allele) is True


def test_unknown_keyword_arguments_are_ignored(trio: Family) -> None:
    allele = make_allele(trio)

    assert RawFamilyVariants.filter_allele(
        allele, no_such_filter=False, regions=[]) is True


# inheritance

def test_inheritance_matcher_gets_or_of_member_inheritance(
    trio: Family,
) -> None:
    allele = make_allele(trio)
    matcher = RecordingMatcher()

    result = RawFamilyVariants.filter_allele(allele, inheritance=[matcher])

    assert result is True
    assert matcher.calls == [
        (Inheritance.unknown.value | Inheritance.denovo.value, None)]


def test_inheritance_matcher_rejection_rejects_the_allele(
    trio: Family,
) -> None:
    allele = make_allele(trio)

    assert RawFamilyVariants.filter_allele(
        allele, inheritance=[RecordingMatcher(result=False)]) is False


def test_inheritance_matchers_must_all_accept(trio: Family) -> None:
    allele = make_allele(trio)
    accept = RecordingMatcher(result=True)
    reject = RecordingMatcher(result=False)

    result = RawFamilyVariants.filter_allele(
        allele, inheritance=[accept, reject])

    assert result is False
    assert len(accept.calls) == 1
    assert len(reject.calls) == 1


def test_empty_inheritance_list_accepts_each_allele(trio: Family) -> None:
    allele = make_allele(trio)

    assert RawFamilyVariants.filter_allele(allele, inheritance=[]) is True


# real_attr_filter

@pytest.mark.parametrize(
    "attributes, bounds, expected",
    [
        ({"score": 0.5}, (0.0, 1.0), True),
        ({"score": 1.5}, (0.0, 1.0), False),
        ({}, (0.0, 1.0), False),
        ({"score": None}, (None, 1.0), True),
        ({"score": None}, (0.0, 1.0), False),
    ],
)
def test_real_attr_filter(
    trio: Family,
    attributes: dict[str, Any],
    bounds: tuple[float | None, float | None],
    expected: bool,
) -> None:
    allele = make_allele(trio, attributes=attributes)

    result = RawFamilyVariants.filter_allele(
        allele, real_attr_filter=[("score", bounds)])

    assert result is expected


# frequency_filter

@pytest.mark.parametrize(
    "attributes, bounds, expected",
    [
        ({"af_allele_freq": 0.5}, (None, 1.0), True),
        ({"af_allele_freq": 5.0}, (None, 1.0), False),
        ({}, (None, 1.0), False),
        ({"af_allele_freq": None}, (None, 1.0), True),
        ({"af_allele_freq": None}, (None, None), True),
    ],
)
def test_frequency_filter(
    trio: Family,
    attributes: dict[str, Any],
    bounds: tuple[float | None, float | None],
    expected: bool,
) -> None:
    allele = make_allele(trio, attributes=attributes)

    result = RawFamilyVariants.filter_allele(
        allele, frequency_filter=[("af_allele_freq", bounds)])

    assert result is expected


# ultra_rare

@pytest.mark.parametrize(
    "attributes, expected",
    [
        ({}, False),
        ({"af_allele_count": None}, True),
        ({"af_allele_count": 0}, True),
        ({"af_allele_count": 1}, True),
        ({"af_allele_count": 2}, False),
    ],
)
def test_ultra_rare(
    trio: Family,
    attributes: dict[str, Any],
    expected: bool,
) -> None:
    allele = make_allele(trio, attributes=attributes)

    assert RawFamilyVariants.filter_allele(
        allele, ultra_rare=True) is expected


def test_falsy_ultra_rare_skips_the_allele_count_check(
    trio: Family,
) -> None:
    allele = make_allele(trio, attributes={"af_allele_count": 5})

    assert RawFamilyVariants.filter_allele(allele, ultra_rare=False) is True


# genes and effect_types

def test_no_gene_filter_resets_matched_gene_effects(trio: Family) -> None:
    allele = make_allele(trio, effect=EFFECT_G1_MISSENSE)
    allele.matched_gene_effects = ["old"]

    assert RawFamilyVariants.filter_allele(allele) is True
    assert not allele.matched_gene_effects


@pytest.mark.parametrize("other_filter", [
    {"inheritance": []},
    {"real_attr_filter": []},
    {"frequency_filter": []},
    {"ultra_rare": False},
])
def test_no_gene_filter_with_other_filter_resets_matched_gene_effects(
    trio: Family, other_filter: dict[str, Any],
) -> None:
    allele = make_allele(trio, effect=EFFECT_G1_MISSENSE)
    allele.matched_gene_effects = ["old"]

    assert RawFamilyVariants.filter_allele(allele, **other_filter) is True
    assert not allele.matched_gene_effects


def test_gene_filter_rejects_an_allele_without_effects(
    trio: Family,
) -> None:
    allele = make_allele(trio)

    assert RawFamilyVariants.filter_allele(allele, genes=["g1"]) is False


@pytest.mark.parametrize(
    "genes, effect_types",
    [
        (["g1"], None),
        (None, ["missense"]),
        (["g1"], ["missense"]),
    ],
)
def test_gene_filter_match_sets_matched_gene_effects(
    trio: Family,
    genes: list[str] | None,
    effect_types: list[str] | None,
) -> None:
    allele = make_allele(trio, effect=EFFECT_G1_MISSENSE)

    result = RawFamilyVariants.filter_allele(
        allele, genes=genes, effect_types=effect_types)

    assert result is True
    assert [str(ge) for ge in allele.matched_gene_effects] == ["g1:missense"]


@pytest.mark.parametrize(
    "genes, effect_types",
    [
        (["g2"], None),
        (None, ["synonymous"]),
        (["g1"], ["synonymous"]),
    ],
)
def test_failed_gene_filter_keeps_old_matched_gene_effects(
    trio: Family,
    genes: list[str] | None,
    effect_types: list[str] | None,
) -> None:
    allele = make_allele(trio, effect=EFFECT_G1_MISSENSE)
    allele.matched_gene_effects = ["old"]

    result = RawFamilyVariants.filter_allele(
        allele, genes=genes, effect_types=effect_types)

    assert result is False
    assert allele.matched_gene_effects == ["old"]


def test_failed_real_attr_check_runs_before_the_gene_check(
    trio: Family,
) -> None:
    allele = make_allele(trio, effect=EFFECT_G1_MISSENSE)
    allele.matched_gene_effects = ["old"]

    result = RawFamilyVariants.filter_allele(
        allele, real_attr_filter=[("score", (0.0, 1.0))])

    assert result is False
    assert allele.matched_gene_effects == ["old"]


# variant_type

def test_variant_type_matcher_gets_the_allele_type(trio: Family) -> None:
    allele = make_allele(trio)
    matcher = RecordingMatcher()

    RawFamilyVariants.filter_allele(allele, variant_type=matcher)

    assert matcher.calls == [(Allele.Type.substitution.value, None)]


def test_variant_type_rejection_rejects_the_allele(trio: Family) -> None:
    allele = make_allele(trio)

    assert RawFamilyVariants.filter_allele(
        allele, variant_type=RecordingMatcher(result=False)) is False


def test_variant_type_runs_after_the_gene_check(trio: Family) -> None:
    allele = make_allele(trio)
    matcher = RecordingMatcher()

    result = RawFamilyVariants.filter_allele(
        allele, genes=["g1"], variant_type=matcher)

    assert result is False
    assert not matcher.calls


def test_variant_type_acceptance_passes_a_reference_allele(
    trio: Family,
) -> None:
    allele = make_reference_allele(trio)

    assert RawFamilyVariants.filter_allele(
        allele, variant_type=RecordingMatcher(),
        return_reference=False, return_unknown=False) is True


def test_variant_type_acceptance_skips_the_member_checks(
    trio: Family,
) -> None:
    allele = make_allele(trio)
    roles = RecordingMatcher(result=False)
    sexes = RecordingMatcher(result=False)
    statuses = RecordingMatcher(result=False)

    result = RawFamilyVariants.filter_allele(
        allele, variant_type=RecordingMatcher(), person_ids=[],
        roles=roles, sexes=sexes, affected_statuses=statuses)

    assert result is True
    assert not roles.calls
    assert not sexes.calls
    assert not statuses.calls


# Reference alleles

@pytest.mark.parametrize(
    "return_reference, return_unknown, expected",
    [
        (None, None, False),
        (False, False, False),
        (True, False, True),
        (False, True, True),
        (True, True, True),
    ],
)
def test_reference_allele(
    trio: Family,
    return_reference: bool | None,
    return_unknown: bool | None,
    expected: bool,
) -> None:
    allele = make_reference_allele(trio)

    result = RawFamilyVariants.filter_allele(
        allele,
        return_reference=return_reference, return_unknown=return_unknown)

    assert result is expected


# person_ids

@pytest.mark.parametrize(
    "person_ids, expected",
    [
        (["p1"], True),
        (["d1", "p1"], True),
        (["d1"], False),
        ([], False),
        ([None], True),
    ],
)
def test_person_ids(
    trio: Family,
    person_ids: list[Any],
    expected: bool,
) -> None:
    allele = make_allele(trio)

    assert RawFamilyVariants.filter_allele(
        allele, person_ids=person_ids) is expected


def test_person_ids_none_rejects_an_allele_that_each_member_has(
    trio: Family,
) -> None:
    allele = make_reference_allele(trio)
    person_ids: list[Any] = [None]

    result = RawFamilyVariants.filter_allele(
        allele, person_ids=person_ids, return_reference=True)

    assert result is False


# roles, sexes and affected_statuses

def test_roles_matcher_gets_carrier_roles_and_zygosity(
    trio: Family,
) -> None:
    allele = make_allele(trio, HET_MOM_HOM_PRB)
    matcher = RecordingMatcher()

    result = RawFamilyVariants.filter_allele(allele, roles=matcher)

    assert result is True
    assert matcher.calls == [
        (Role.mom.value | Role.prb.value, allele.zygosity_in_roles)]
    assert allele.zygosity_in_roles != 0


def test_sexes_matcher_gets_carrier_sexes_and_zygosity(
    trio: Family,
) -> None:
    allele = make_allele(trio, HET_MOM_HOM_PRB)
    matcher = RecordingMatcher()

    result = RawFamilyVariants.filter_allele(allele, sexes=matcher)

    assert result is True
    assert matcher.calls == [
        (Sex.F.value | Sex.M.value, allele.zygosity_in_sexes)]
    assert allele.zygosity_in_sexes != 0


def test_statuses_matcher_gets_carrier_statuses_and_zygosity(
    trio: Family,
) -> None:
    allele = make_allele(trio, HET_MOM_HOM_PRB)
    matcher = RecordingMatcher()

    result = RawFamilyVariants.filter_allele(
        allele, affected_statuses=matcher)

    assert result is True
    assert matcher.calls == [(
        Status.unaffected.value | Status.affected.value,
        allele.zygosity_in_status,
    )]
    assert allele.zygosity_in_status != 0


@pytest.mark.parametrize(
    "argument", ["roles", "sexes", "affected_statuses"])
def test_member_matcher_gets_zero_when_no_member_carries_the_allele(
    trio: Family,
    argument: str,
) -> None:
    allele = make_allele(trio, ALL_REFERENCE)
    matcher = RecordingMatcher()
    filters: dict[str, Any] = {argument: matcher}

    result = RawFamilyVariants.filter_allele(allele, **filters)

    assert result is True
    assert matcher.calls == [(0, 0)]


@pytest.mark.parametrize(
    "argument", ["roles", "sexes", "affected_statuses"])
def test_member_matcher_rejection_rejects_the_allele(
    trio: Family,
    argument: str,
) -> None:
    allele = make_allele(trio)
    filters: dict[str, Any] = {argument: RecordingMatcher(result=False)}

    result = RawFamilyVariants.filter_allele(allele, **filters)

    assert result is False


def test_member_checks_run_in_order_roles_sexes_statuses(
    trio: Family,
) -> None:
    allele = make_allele(trio)
    roles = RecordingMatcher(result=True)
    sexes = RecordingMatcher(result=False)
    statuses = RecordingMatcher(result=True)

    result = RawFamilyVariants.filter_allele(
        allele, roles=roles, sexes=sexes, affected_statuses=statuses)

    assert result is False
    assert len(roles.calls) == 1
    assert len(sexes.calls) == 1
    assert not statuses.calls
