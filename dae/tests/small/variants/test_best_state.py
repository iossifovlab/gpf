# pylint: disable=C0114,C0116,protected-access,fixme, R0917, W0621
from io import StringIO

import numpy as np
import pytest
from dae.pedigrees.family import Family
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.variant_utils import GenotypeType
from dae.variants.family_variant import FamilyAllele
from dae.variants.variant import SummaryAllele

PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
"""


@pytest.fixture
def sample_family() -> Family:
    families_loader = FamiliesLoader(StringIO(PED1), ped_sep=",")
    families = families_loader.load()
    family = families["f1"]
    assert len(family.trios) == 1
    return family


@pytest.mark.parametrize(
    "chromosome, position, reference, alternative, "
    "allele_index, allele_count, genotype, expected",
    [
        (
            "chr1",
            0,
            "A",
            "T",
            1,
            2,
            np.array([[0, 0, 0], [0, 0, 1]], dtype=GenotypeType),
            np.array([[2, 2, 1], [0, 0, 1]], dtype=GenotypeType),
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            1,
            2,
            np.array([[0, 0, 0], [0, 1, 1]], dtype=GenotypeType),
            np.array([[2, 1, 1], [0, 1, 1]], dtype=GenotypeType),
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            1,
            2,
            np.array([[0, 0, 1], [0, 0, 1]], dtype=GenotypeType),
            np.array([[2, 2, 0], [0, 0, 2]], dtype=GenotypeType),
        ),
    ],
)
def test_allele_best_state(
    chromosome: str,
    position: int,
    reference: str,
    alternative: str,
    allele_index: int,
    allele_count: int,
    genotype: np.ndarray,
    expected: np.ndarray,
    sample_family: Family,
) -> None:

    fa = FamilyAllele(
        SummaryAllele(
            chromosome, position, reference,
            alternative=alternative,
            summary_index=0, allele_index=allele_index,
        ),
        sample_family,
        genotype=genotype,
        best_state=None,
    )
    fa.update_attributes({"allele_count": allele_count})
    assert np.array_equal(fa.best_state, expected)
