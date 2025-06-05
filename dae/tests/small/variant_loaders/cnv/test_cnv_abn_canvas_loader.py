# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap
from typing import TextIO, cast

import pytest

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import convert_to_tab_separated
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance
from dae.variants.core import Allele
from dae.variants.family_variant import FamilyAllele
from dae.variants_loaders.cnv.loader import CNVLoader


@pytest.fixture
def abn_families() -> FamiliesData:
    ped_content = io.StringIO(convert_to_tab_separated(
        """
            familyId personId dadId	 momId	sex status role
            f1       p1       0      0      2   2      prb
            f2       p2       0      0      1   2      prb
        """))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families


@pytest.fixture
def canvas_cnv() -> TextIO:
    return io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        study_id family_id person_id location   variant
        st1      f1        p1        chr1:10-50 LOSS
        st1      f2        p2        chr2:10-50 GAIN
        """,
    )))


@pytest.mark.parametrize(
    "transmission_type,expected_inheritance", [
        ("transmitted", Inheritance.unknown),
        ("denovo", Inheritance.denovo),
    ],
)
def test_cnv_loader_expected_inheritance(
    abn_families: FamiliesData,
    canvas_cnv: str,
    acgt_genome_38: ReferenceGenome,
    transmission_type: str,
    expected_inheritance: Inheritance,
) -> None:

    loader = CNVLoader(
        abn_families, [canvas_cnv], genome=acgt_genome_38,
        params={
            "cnv_family_id": "family_id",
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": transmission_type,
        },
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2
    for _sv, fvs in variants:
        for fv in fvs:
            for aa in fv.alt_alleles:
                fa = cast(FamilyAllele, aa)
                assert expected_inheritance in fa.inheritance_in_members


@pytest.mark.parametrize(
    "variant_index,expected_variant_type", [
        (0, Allele.Type.large_deletion),
        (1, Allele.Type.large_duplication),
    ],
)
def test_cnv_loader_expected_variant_type(
    abn_families: FamiliesData,
    canvas_cnv: TextIO,
    acgt_genome_38: ReferenceGenome,
    variant_index: int,
    expected_variant_type: Allele.Type,
) -> None:
    loader = CNVLoader(
        abn_families, [canvas_cnv], genome=acgt_genome_38,
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
        },
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2
    _sv, fvs = variants[variant_index]
    for fv in fvs:
        for fa in fv.alt_alleles:
            assert expected_variant_type == fa.variant_type


@pytest.mark.parametrize(
    "add_chrom_prefix,region,expected", [
        (None, "chr1", 1),
        (None, "chr2", 1),
        (None, "chr3", 0),
        ("chr", "1", 0),
        ("chr", "2", 0),
    ],
)
def test_cnv_loader_regions(
    abn_families: FamiliesData, canvas_cnv: TextIO,
    acgt_genome_38: ReferenceGenome,
    add_chrom_prefix: str | None,
    region: str,
    expected: int,
) -> None:

    loader = CNVLoader(
        abn_families, [canvas_cnv], genome=acgt_genome_38,
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
            "add_chrom_prefix": add_chrom_prefix,
        },
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2

    loader.reset_regions([Region.from_str(region)])
    family_variants = list(loader.family_variants_iterator())
    assert len(family_variants) == expected


@pytest.mark.parametrize(
    "add_chrom_prefix,region,expected", [
        (None, "chr1", 1),
        (None, "chr2", 1),
        (None, "chr3", 0),
        ("chr", "chr1", 0),
        ("chr", "chr2", 0),
    ],
)
def test_cnv_loader_constructor_regions(
    abn_families: FamiliesData,
    canvas_cnv: TextIO,
    acgt_genome_38: ReferenceGenome,
    add_chrom_prefix: str | None,
    region: str, expected: int,
) -> None:

    loader = CNVLoader(
        abn_families, [canvas_cnv], genome=acgt_genome_38,
        regions=[Region.from_str(region)],
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
            "add_chrom_prefix": add_chrom_prefix,
        },
    )

    variants = list(loader.family_variants_iterator())
    assert len(variants) == expected


@pytest.mark.parametrize(
    "region,expected", [
        ("chr1", 1),
        ("chr2", 1),
        ("chr3", 0),
        ("chrchr1", 0),
        ("chrchr2", 0),
    ],
)
def test_cnv_loader_del_chrom_prefix_regions(
    abn_families: FamiliesData,
    acgt_genome_38: ReferenceGenome,
    region: str,
    expected: int,
) -> None:

    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        study_id  family_id  person_id  location       variant
        st1       f1         p1         chrchr1:10-20  LOSS
        st1       f2         p2         chrchr2:10-20  GAIN
        """,
    )))

    loader = CNVLoader(
        abn_families, [content],
        genome=acgt_genome_38,
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
            "del_chrom_prefix": "chr",
        },
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2

    loader.reset_regions([Region.from_str(region)])
    family_variants = list(loader.family_variants_iterator())
    assert len(family_variants) == expected
