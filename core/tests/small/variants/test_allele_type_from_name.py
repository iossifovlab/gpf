# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from gpf.variants.core import Allele
from gpf.variants.variant import allele_type_from_name


@pytest.mark.parametrize(
    "name, expected",
    [
        ("sub", Allele.Type.substitution),
        ("substitution", Allele.Type.substitution),
        ("ins", Allele.Type.small_insertion),
        ("insertion", Allele.Type.small_insertion),
        ("del", Allele.Type.small_deletion),
        ("deletion", Allele.Type.small_deletion),
        ("comp", Allele.Type.complex),
        ("complex", Allele.Type.complex),
        ("cnv_p", Allele.Type.large_duplication),
        ("cnv+", Allele.Type.large_duplication),
        ("large_duplication", Allele.Type.large_duplication),
        ("cnv_m", Allele.Type.large_deletion),
        ("cnv-", Allele.Type.large_deletion),
        ("large_deletion", Allele.Type.large_deletion),
        ("tr", Allele.Type.tandem_repeat),
        ("tandem_repeat", Allele.Type.tandem_repeat),
    ],
)
def test_allele_type_from_name_maps_known_name(
    name: str, expected: Allele.Type,
) -> None:
    assert allele_type_from_name(name) is expected


def test_allele_type_from_name_ignores_case_and_surrounding_spaces() -> None:
    assert allele_type_from_name(" SUB ") is Allele.Type.substitution


def test_allele_type_from_name_rejects_unknown_name() -> None:
    with pytest.raises(
        ValueError, match=r"^unexpected variant type: unknown$",
    ):
        allele_type_from_name(" Unknown ")
