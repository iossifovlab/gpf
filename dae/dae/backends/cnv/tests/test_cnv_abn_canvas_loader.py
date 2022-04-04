import textwrap
from dae.backends.cnv.loader import CNVLoader
import pytest
import io

from dae.variants.attributes import Inheritance
from dae.genomic_resources.test_tools import convert_to_tab_separated
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
        st1       p1         p1         1:10000000-2000000  LOSS
        st1       p2         p2         2:10000000-2000000  GAIN
        """
    )))
    return content


@pytest.mark.parametrize(
    "transmission_type,expected_inheritance", [
        ("transmitted", Inheritance.unknown),
        ("denovo", Inheritance.denovo),
    ]
)
def test_cnv_loader_simple(
        abn_families, canvas_cnv, gpf_instance_2013,
        transmission_type, expected_inheritance):

    loader = CNVLoader(
        abn_families, canvas_cnv, gpf_instance_2013.reference_genome,
        params={
           "cnv_person_id": "person_id",
           "cnv_family_id": "family_id",
           "cnv_location": "location",
           "cnv_variant_type": "variant",
           "cnv_plus_values": ["GAIN"],
           "cnv_minus_values": ["LOSS"],
           "cnv_inheritance_type": transmission_type,
        }
    )

    variants = list(loader.full_variants_iterator())
    print(variants)
    assert len(variants) == 2
    for sv, fvs in variants:
        for fv in fvs:
            for fa in fv.alt_alleles:
                assert expected_inheritance in fa.inheritance_in_members
