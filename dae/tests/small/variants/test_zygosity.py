# pylint: disable=R0917,C0114,C0116,protected-access,fixme,W0621
from io import StringIO

import numpy as np
import pytest
from dae.pedigrees.family import Family
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.variant_utils import GenotypeType
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant

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
    "allele_count, genotype, expected",
    [
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 0], [0, 1, 1]], dtype=GenotypeType),
            2 | (2 << 2),
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 1], [0, 0, 1]], dtype=GenotypeType),
            4,
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 1], [0, 1, 1]], dtype=GenotypeType),
            2 | (1 << 2),
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 0], [0, 0, 0]], dtype=GenotypeType),
            0,
        ),
    ],
)
def test_fv_zygosity_in_status(
    chromosome: str,
    position: int,
    reference: str,
    alternative: str,
    allele_count: int,
    genotype: np.ndarray,
    expected: np.ndarray,
    sample_family: Family,
) -> None:

    sv = SummaryVariant(
        [
            SummaryAllele(
                chromosome, position, reference, None,
                summary_index=0, allele_index=0,
            ),
            SummaryAllele(
                chromosome, position, reference, alternative,
                summary_index=0, allele_index=1,
            ),
        ],
    )

    fv = FamilyVariant(
        sv,
        sample_family,
        genotype,
        None,
    )
    fv.update_attributes({"allele_count": [allele_count]})
    assert fv.zygosity_in_status == expected


@pytest.mark.parametrize(
    "chromosome, position, reference, alternative, "
    "allele_count, genotype, expected",
    [
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 0], [0, 1, 1]], dtype=GenotypeType),
            (2 << (4 * 2)) | (2 << (7 * 2)),  # mom and prb
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 1], [0, 0, 1]], dtype=GenotypeType),
            (1 << (7 * 2)),  # prb
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 1], [0, 1, 1]], dtype=GenotypeType),
            (2 << (4 * 2)) | (1 << (7 * 2)),  # mom and prb
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 0], [0, 0, 0]], dtype=GenotypeType),
            0,
        ),
    ],
)
def test_fv_zygosity_in_roles(
    chromosome: str,
    position: int,
    reference: str,
    alternative: str,
    allele_count: int,
    genotype: np.ndarray,
    expected: np.ndarray,
    sample_family: Family,
) -> None:

    sv = SummaryVariant(
        [
            SummaryAllele(
                chromosome, position, reference, None,
                summary_index=0, allele_index=0,
            ),
            SummaryAllele(
                chromosome, position, reference, alternative,
                summary_index=0, allele_index=1,
            ),
        ],
    )

    fv = FamilyVariant(
        sv,
        sample_family,
        genotype,
        None,
    )
    fv.update_attributes({"allele_count": [allele_count]})
    assert fv.zygosity_in_roles == expected


@pytest.mark.parametrize(
    "chromosome, position, reference, alternative, "
    "allele_count, genotype, expected",
    [
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 1], [0, 0, 1]], dtype=GenotypeType),
            (1 << (0 * 2)),  # homozyg male prb
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 1, 0], [0, 1, 0]], dtype=GenotypeType),
            (1 << (1 * 2)),  # homozyg female mom
        ),
        (
            "chr1",
            0,
            "A",
            "T",
            2,
            np.array([[0, 0, 1], [1, 1, 1]], dtype=GenotypeType),
            (1 << (0 * 2)) | (2 << (1 * 2)) | (2 << (0 * 2)),
            # homozyg prb, heterozyg mom, heterozyg dad
        ),
    ],
)
def test_zygosity_in_sexes(
    chromosome: str,
    position: int,
    reference: str,
    alternative: str,
    allele_count: int,
    genotype: np.ndarray,
    expected: np.ndarray,
    sample_family: Family,
) -> None:

    sv = SummaryVariant(
        [
            SummaryAllele(
                chromosome, position, reference, None,
                summary_index=0, allele_index=0,
            ),
            SummaryAllele(
                chromosome, position, reference, alternative,
                summary_index=0, allele_index=1,
            ),
        ],
    )

    fv = FamilyVariant(
        sv,
        sample_family,
        genotype,
        None,
    )
    fv.update_attributes({"allele_count": [allele_count]})
    assert fv.zygosity_in_sexes == expected
