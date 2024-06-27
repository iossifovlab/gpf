# pylint: disable=W0621,C0114,C0116,W0212,W0613
from io import StringIO
from typing import cast

import numpy as np
import pytest

from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.family import Family
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import TransmissionType
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant


@pytest.fixture(scope="module")
def genotype() -> np.ndarray:
    return np.array([[0, 0, 0], [0, 0, 0]], dtype=np.int8)


PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
"""

PED2 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f2,          d2,          0,        0,        1,     1,         dad
f2,          m2,          0,        0,        2,     1,         mom
f2,          p2,          d2,       m2,       1,     2,         prb
"""


@pytest.fixture(scope="module")
def fam1() -> Family:
    families_loader = FamiliesLoader(StringIO(PED1), ped_sep=",")
    families = families_loader.load()
    family = families["f1"]

    assert len(family.trios) == 1
    return family


@pytest.fixture(scope="module")
def fam2() -> Family:
    families_loader = FamiliesLoader(StringIO(PED2), ped_sep=",")
    families = families_loader.load()
    family = families["f2"]

    assert len(family.trios) == 1
    return family


summary_alleles_chr1 = [
    SummaryAllele("1", 11539, "T", None, 0, 0),
    SummaryAllele("1", 11539, "T", "TA", 0, 1),
    SummaryAllele("1", 11539, "T", "TG", 0, 2),
]

summary_alleles_chr2 = [
    SummaryAllele("2", 11539, "T", None, 0, 0),
    SummaryAllele("2", 11539, "T", "TA", 0, 1),
    SummaryAllele("2", 11539, "T", "TG", 0, 2),
]


@pytest.mark.parametrize(
    "chromosomes, region_length, summary_alleles, expected",
    [
        (["1", "2"], 1000, summary_alleles_chr1, "1_11"),
        (["1", "2"], 1000, summary_alleles_chr2, "2_11"),
        (["1"], 1000, summary_alleles_chr1, "1_11"),
        (["2"], 1000, summary_alleles_chr1, "other_11"),
    ],
)
def test_parquet_region_bin(
    fam1: Family,
    genotype: np.ndarray,
    chromosomes: list[str],
    region_length: int,
    summary_alleles: list[SummaryAllele],
    expected: str,
) -> None:
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant(sv, fam1, genotype, None)
    part_desc = PartitionDescriptor(chromosomes, region_length)
    region_bin = part_desc.make_region_bin(fv.chrom, fv.position)
    for aa in fv.alleles:
        fa = cast(FamilyAllele, aa)
        assert region_bin == expected
        partition = part_desc.schema1_partition(fa)
        assert partition == [("region_bin", region_bin)]


def test_parquet_family_bin(
    fam1: Family, fam2: Family,
    genotype: np.ndarray,
) -> None:
    sv = SummaryVariant(summary_alleles_chr1)
    fv1 = FamilyVariant(sv, fam1, genotype, None)
    fv2 = FamilyVariant(sv, fam2, genotype, None)

    family_bin_size = 10
    part_desc = PartitionDescriptor(["1"], 1000, family_bin_size)
    for a1, a2 in zip(fv1.alleles, fv2.alleles):
        fa1 = cast(FamilyAllele, a1)
        fa2 = cast(FamilyAllele, a2)
        assert part_desc.make_family_bin(fa1.family_id) == 9
        assert part_desc.make_family_bin(fa2.family_id) == 6
        partition1 = part_desc.schema1_partition(fa1)
        partition2 = part_desc.schema1_partition(fa2)
        assert partition1 == [("region_bin", "1_11"), ("family_bin", "9")]
        assert partition2 == [("region_bin", "1_11"), ("family_bin", "6")]


@pytest.mark.parametrize(
    "attributes, rare_boundary, expected",
    [
        ({"af_allele_count": 1}, 5, "1"),
        ({"af_allele_count": 10, "af_allele_freq": 2}, 5, "2"),
        ({"af_allele_count": 10, "af_allele_freq": 5}, 5, "2"),
        ({"af_allele_count": 10, "af_allele_freq": 6}, 5, "3"),
        ({"af_allele_count": 10, "af_allele_freq": 50}, 10, "3"),
    ],
)
def test_parquet_frequency_bin(
    fam1: Family, genotype: np.ndarray,
    attributes: dict[str, int],
    rare_boundary: int,
    expected: str,
) -> None:
    summary_alleles = [
        SummaryAllele("1", 11539, "T", None, 0, 0, attributes=attributes),
    ] * 3
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant(sv, fam1, genotype, None)
    part_desc = PartitionDescriptor(
        ["1"], 1000, rare_boundary=rare_boundary)

    for fa in fv.alleles:
        allele_count = fa.get_attribute("af_allele_count")
        allele_freq = fa.get_attribute("af_allele_freq")
        is_denovo = fa.transmission_type == TransmissionType.denovo

        assert part_desc.make_frequency_bin(
            allele_count, allele_freq,
            is_denovo=is_denovo) == expected
        partition = part_desc.schema1_partition(cast(FamilyAllele, fa))
        assert partition == [
            ("region_bin", "1_11"), ("frequency_bin", expected)]
