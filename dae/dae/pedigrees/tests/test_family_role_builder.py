import pytest
from dae.pedigrees.family_role_builder import FamilyRoleBuilder
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Role


# TODO: Organize into 1 test
@pytest.mark.parametrize(
    'ped_file',
    ['pedigrees/pedigree_no_role_A.ped', 'pedigrees/pedigree_no_role_B.ped'])
def test_mom_dad_child_sibling_roles(fixture_dirname, ped_file):
    families = FamiliesLoader.load_pedigree_file(fixture_dirname(ped_file))
    family = families.get('f1')
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.dad
    assert members[1].role == Role.mom
    assert members[2].role == Role.prb
    assert members[3].role == Role.sib


def test_paternal_and_maternal_grandparents(fixture_dirname):
    ped_file = fixture_dirname('pedigrees/pedigree_no_role_C.ped')
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get('f1')
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[0].role == Role.maternal_grandfather
    assert members[1].role == Role.maternal_grandmother
    assert members[2].role == Role.paternal_grandfather
    assert members[3].role == Role.paternal_grandmother


def test_child_and_spouse(fixture_dirname):
    ped_file = fixture_dirname('pedigrees/pedigree_no_role_D.ped')
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get('f1')
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[4].role == Role.spouse
    assert members[5].role == Role.child


def test_maternal_and_paternal_aunts_and_uncles(fixture_dirname):
    ped_file = fixture_dirname('pedigrees/pedigree_no_role_E.ped')
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get('f1')
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[6].role == Role.maternal_aunt
    assert members[7].role == Role.maternal_uncle
    assert members[8].role == Role.paternal_aunt
    assert members[9].role == Role.paternal_uncle


def test_maternal_and_paternal_cousins(fixture_dirname):
    ped_file = fixture_dirname('pedigrees/pedigree_no_role_F.ped')
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get('f1')
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[12].role == Role.maternal_cousin
    assert members[13].role == Role.paternal_cousin


def test_stepmom_and_stepdad(fixture_dirname):
    ped_file = fixture_dirname('pedigrees/pedigree_no_role_G.ped')
    families = FamiliesLoader.load_pedigree_file(ped_file)
    family = families.get('f1')
    role_builder = FamilyRoleBuilder(family)
    role_builder.build_roles()
    members = family.full_members

    assert members[2].role == Role.step_dad
    assert members[3].role == Role.step_mom


def test_handling_of_family_with_only_prb_role(fixture_dirname):
    pass
