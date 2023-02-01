# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.pedigrees.family_role_builder import FamilyRoleBuilder
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Role


# TODO: Organize into 1 test
@pytest.mark.parametrize(
    "ped_file",
    ["pedigrees/pedigree_no_role_A.ped", "pedigrees/pedigree_no_role_B.ped"],
)
def test_mom_dad_child_sibling_roles(fixture_dirname, ped_file):
    families = FamiliesLoader.load_pedigree_file(fixture_dirname(ped_file))
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.dad
    assert members[1].role == Role.mom
    assert members[2].role == Role.prb
    assert members[3].role == Role.sib


def test_paternal_and_maternal_grandparents(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_no_role_C.ped")
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.maternal_grandfather
    assert members[1].role == Role.maternal_grandmother
    assert members[2].role == Role.paternal_grandfather
    assert members[3].role == Role.paternal_grandmother
    assert members[4].role == Role.dad
    assert members[5].role == Role.mom
    assert members[6].role == Role.prb
    assert members[7].role == Role.sib


def test_child_and_spouse(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_no_role_D.ped")
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.dad
    assert members[1].role == Role.mom
    assert members[2].role == Role.prb
    assert members[3].role == Role.sib
    assert members[4].role == Role.spouse
    assert members[5].role == Role.child


def test_maternal_and_paternal_aunts_and_uncles(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_no_role_E.ped")
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.maternal_grandfather
    assert members[1].role == Role.maternal_grandmother
    assert members[2].role == Role.paternal_grandfather
    assert members[3].role == Role.paternal_grandmother
    assert members[4].role == Role.dad
    assert members[5].role == Role.mom
    assert members[6].role == Role.maternal_aunt
    assert members[7].role == Role.maternal_uncle
    assert members[8].role == Role.paternal_aunt
    assert members[9].role == Role.paternal_uncle
    assert members[10].role == Role.prb
    assert members[11].role == Role.sib


def test_maternal_and_paternal_cousins(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_no_role_F.ped")
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.maternal_grandfather
    assert members[1].role == Role.maternal_grandmother
    assert members[2].role == Role.paternal_grandfather
    assert members[3].role == Role.paternal_grandmother
    assert members[4].role == Role.dad
    assert members[5].role == Role.mom
    assert members[6].role == Role.maternal_aunt
    assert members[7].role == Role.unknown
    assert members[8].role == Role.unknown
    assert members[9].role == Role.paternal_uncle
    assert members[10].role == Role.prb
    assert members[11].role == Role.sib
    assert members[12].role == Role.maternal_cousin
    assert members[13].role == Role.paternal_cousin


def test_stepmom_and_stepdad(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_no_role_G.ped")
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.dad
    assert members[1].role == Role.mom

    assert members[2].role == Role.step_dad
    assert members[3].role == Role.step_mom

    assert members[4].role == Role.maternal_half_sibling
    assert members[5].role == Role.paternal_half_sibling
    assert members[6].role == Role.prb
    assert members[7].role == Role.sib


def test_handling_of_family_with_only_prb_role(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_prb_only.ped")
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.dad
    assert members[1].role == Role.mom
    assert members[2].role == Role.prb
    assert members[3].role == Role.sib


def test_handling_of_large_family_with_only_prb_role(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_prb_only_large.ped")
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get("f1")
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.maternal_grandfather
    assert members[1].role == Role.maternal_grandmother
    assert members[2].role == Role.paternal_grandfather
    assert members[3].role == Role.paternal_grandmother
    assert members[4].role == Role.dad
    assert members[5].role == Role.mom
    assert members[6].role == Role.maternal_aunt
    assert members[7].role == Role.unknown
    assert members[8].role == Role.unknown
    assert members[9].role == Role.paternal_uncle
    assert members[10].role == Role.prb
    assert members[11].role == Role.sib
    assert members[12].role == Role.maternal_cousin
    assert members[13].role == Role.paternal_cousin


def test_proband_column(fixture_dirname):
    ped_file = fixture_dirname("pedigrees/pedigree_no_role_F.ped")
    loader = FamiliesLoader(ped_file, **{"ped_no_role": True})
    families = loader.load()

    for person in families.persons.values():
        assert not person.has_attr("proband")

    ped_file = fixture_dirname("pedigrees/pedigree_no_role_H.ped")
    loader = FamiliesLoader(ped_file, **{"ped_no_role": True})
    families = loader.load()

    for person in families.persons.values():
        assert person.has_attr("proband")

    family = families.get("f1")
    assert family is not None

    members = family.full_members

    assert members[0].role == Role.maternal_grandfather
    assert members[1].role == Role.maternal_grandmother
    assert members[2].role == Role.paternal_grandfather
    assert members[3].role == Role.paternal_grandmother
    assert members[4].role == Role.dad
    assert members[5].role == Role.mom
    assert members[6].role == Role.maternal_aunt
    assert members[7].role == Role.unknown
    assert members[8].role == Role.unknown
    assert members[9].role == Role.paternal_uncle
    assert members[10].role == Role.prb
    assert members[11].role == Role.sib
    assert members[12].role == Role.maternal_cousin
    assert members[13].role == Role.paternal_cousin
