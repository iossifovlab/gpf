# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.pedigrees.testing import build_families_data
from dae.pedigrees.family_tag_builder import FamilyTagsBuilder

@pytest.mark.parametrize("tag,value", [
    ("tag_nuclear_family", True),
    ("tag_quad_family", False),
    ("tag_trio_family", False),
    ("tag_simplex_family", False),
    ("tag_multiplex_family", True),
    ("tag_control_family", False),
    ("tag_affected_dad_family", False),
    ("tag_affected_mom_family", False),
    ("tag_affected_prb_family", True),
    ("tag_affected_sib_family", True),
    ("tag_male_prb_family", False),
    ("tag_female_prb_family", True),
    ("tag_missing_mom_family", False),
    ("tag_missing_dad_family", False),
    ("tags", "tag_affected_prb_family;tag_affected_sib_family;"
     "tag_female_prb_family;tag_multiplex_family;tag_nuclear_family")
])
def test_family_tags_builder_simple(tag, value):

    families = build_families_data(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     1   1      sib
            f1       s2       d1     m1     2   2      sib
        """)

    tagger = FamilyTagsBuilder()
    tagger.tag_families_data(families)

    ped_df = families.ped_df
    assert all(ped_df[tag] == value)
