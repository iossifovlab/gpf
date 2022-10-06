# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap
import pytest

from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants.attributes import Inheritance
from dae.variants.core import Allele

from dae.testing import convert_to_tab_separated
from dae.pedigrees.loader import FamiliesLoader


@pytest.fixture
def abn_families():
    ped_content = io.StringIO(convert_to_tab_separated(
        """
            familyId personId dadId	 momId	sex status role
            p1       p1       0      0      2   2      prb
            p2       p2       0      0      1   2      prb
        """))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families


@pytest.fixture
def canvas_cnv():
    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        study_id  family_id  person_id  location            variant
        st1       f1         p1         1:10000000-2000000  LOSS
        st1       f2         p2         2:10000000-2000000  GAIN
        """
    )))
    return content


@pytest.mark.parametrize(
    "transmission_type,expected_inheritance", [
        ("transmitted", Inheritance.unknown),
        ("denovo", Inheritance.denovo),
    ]
)
def test_cnv_loader_expected_inheritance(
        abn_families, canvas_cnv, gpf_instance_2013,
        transmission_type, expected_inheritance):

    loader = CNVLoader(
        abn_families, canvas_cnv, gpf_instance_2013.reference_genome,
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": transmission_type,
        }
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2
    for _sv, fvs in variants:
        for fv in fvs:
            for fa in fv.alt_alleles:
                assert expected_inheritance in fa.inheritance_in_members


@pytest.mark.parametrize(
    "variant_index,expected_variant_type", [
        (0, Allele.Type.large_deletion),
        (1, Allele.Type.large_duplication),
    ]
)
def test_cnv_loader_expected_variant_type(
        abn_families, canvas_cnv, gpf_instance_2013,
        variant_index, expected_variant_type):

    loader = CNVLoader(
        abn_families, canvas_cnv, gpf_instance_2013.reference_genome,
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
        }
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2
    _sv, fvs = variants[variant_index]
    for fv in fvs:
        for fa in fv.alt_alleles:
            assert expected_variant_type == fa.variant_type


@pytest.mark.parametrize(
    "add_chrom_prefix,region,expected", [
        (None, "1", 1),
        (None, "2", 1),
        (None, "3", 0),
        ("chr", "chr1", 1),
        ("chr", "chr2", 1),
        ("chr", "1", 0),
        ("chr", "2", 0),
    ]
)
def test_cnv_loader_regions(
        abn_families, canvas_cnv, gpf_instance_2013,
        add_chrom_prefix, region, expected):

    loader = CNVLoader(
        abn_families, canvas_cnv, gpf_instance_2013.reference_genome,
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
            "add_chrom_prefix": add_chrom_prefix,
        }
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2

    loader.reset_regions(region)
    variants = list(loader.family_variants_iterator())
    assert len(variants) == expected


@pytest.mark.parametrize(
    "add_chrom_prefix,region,expected", [
        (None, "1", 1),
        (None, "2", 1),
        (None, "3", 0),
        ("chr", "chr1", 1),
        ("chr", "chr2", 1),
        ("chr", "1", 0),
        ("chr", "2", 0),
    ]
)
def test_cnv_loader_constructor_regions(
        abn_families, canvas_cnv, gpf_instance_2013,
        add_chrom_prefix, region, expected):

    loader = CNVLoader(
        abn_families, canvas_cnv, gpf_instance_2013.reference_genome,
        regions=[region],
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
            "add_chrom_prefix": add_chrom_prefix,
        }
    )

    variants = list(loader.family_variants_iterator())
    assert len(variants) == expected


@pytest.mark.parametrize(
    "region,expected", [
        ("1", 1),
        ("2", 1),
        ("3", 0),
        ("chr1", 0),
        ("chr2", 0),
    ]
)
def test_cnv_loader_del_chrom_prefix_regions(
        abn_families, gpf_instance_2013, region, expected):

    content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
        study_id  family_id  person_id  location               variant
        st1       p1         p1         chr1:10000000-2000000  LOSS
        st1       p2         p2         chr2:10000000-2000000  GAIN
        """
    )))

    loader = CNVLoader(
        abn_families, content, gpf_instance_2013.reference_genome,
        params={
            "cnv_person_id": "person_id",
            "cnv_location": "location",
            "cnv_variant_type": "variant",
            "cnv_plus_values": ["GAIN"],
            "cnv_minus_values": ["LOSS"],
            "cnv_transmission_type": "transmitted",
            "del_chrom_prefix": "chr",
        }
    )

    variants = list(loader.full_variants_iterator())
    assert len(variants) == 2

    loader.reset_regions(region)
    variants = list(loader.family_variants_iterator())
    assert len(variants) == expected
