# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.pedigrees.families_data import tag_families_data
from dae.pedigrees.family import FamilyTag
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.testing import build_families_data


@pytest.mark.parametrize("tag_label,value", [
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
])
def test_family_tags_builder_simple(tag_label: str, value: bool) -> None:

    families = build_families_data(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     1   1      sib
            f1       s2       d1     m1     2   2      sib
        """)

    tag_families_data(families)

    ped_df = families.ped_df
    assert all(ped_df[tag_label] == value)


def test_family_types_simple() -> None:

    families = build_families_data(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1.1     d1     m1     1   1      sib
            f1       s1.2     d1     m1     2   2      sib
            f2       m2       0      0      2   1      mom
            f2       d2       0      0      1   1      dad
            f2       p2       d2     m2     2   2      prb
            f2       s2.1     d2     m2     1   1      sib
            f3       m3       0      0      2   1      mom
            f3       d3       0      0      1   1      dad
            f3       p3       d3     m3     2   2      prb
            f3       s3.1     d3     m3     1   1      sib
        """)

    tag_families_data(families)

    ped_df = families.ped_df

    # assert all(
    #     ped_df[ped_df.family_id == "f2"]["tag_family_type"] == "type#1")
    # assert all(
    #     ped_df[ped_df.family_id == "f3"]["tag_family_type"] == "type#1")
    # assert all(
    #     ped_df[ped_df.family_id == "f1"]["tag_family_type"] == "type#2")

    assert all(
        ped_df[ped_df.family_id == "f2"]["tag_family_type_full"]
        == "4:dad.M.unaffected:mom.F.unaffected:prb.F.affected:"
        "sib.M.unaffected")


def test_family_tags_save_load(tmp_path: pathlib.Path) -> None:
    families = build_families_data(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     1   1      sib
            f1       s2       d1     m1     2   2      sib
        """)

    tag_families_data(families)

    FamiliesLoader.save_pedigree(families, str(tmp_path / "families.ped"))
    assert (tmp_path / "families.ped").exists()

    loaded_families = FamiliesLoader.load_pedigree_file(
        str(tmp_path / "families.ped"),
        pedigree_params={"ped_tags": False},
    )
    assert "f1" in loaded_families

    fam1 = loaded_families["f1"]
    for person in fam1.persons.values():
        assert person.has_tag(FamilyTag.NUCLEAR)
        assert person.has_tag(FamilyTag.UNAFFECTED_DAD)
        assert person.has_tag(FamilyTag.UNAFFECTED_MOM)
        assert person.has_tag(FamilyTag.AFFECTED_PRB)
        assert person.has_tag(FamilyTag.AFFECTED_SIB)
        assert person.has_tag(FamilyTag.UNAFFECTED_SIB)
