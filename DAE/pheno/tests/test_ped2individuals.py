"""
Created on Oct 16, 2017

@author: lubo
"""
from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
import abc
import pytest
from pheno.prepare.ped2individuals import PedigreeToFamily, NoProband
from collections import defaultdict
from variants.attributes import Role, Sex, Status
import itertools
from future.utils import with_metaclass


@pytest.fixture(scope="module")
def ped2family():
    return PedigreeToFamily()


def assert_role_at_index(individuals, index, role):
    assert individuals[index].individual.role == role


class BaseFamily(with_metaclass(abc.ABCMeta, object)):
    FAMILY_ID = 'some_family'

    def family_members(self, families):
        assert self.FAMILY_ID in families
        return families[self.FAMILY_ID]


class TestNuclearFamily(BaseFamily):

    FAMILY_ID = 'nuclear'

    def test_all_have_roles(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))
        for individual in individuals:
            assert individual.individual.role != Role.unknown

    def test_father_role_is_correctly_set(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 4

        assert_role_at_index(individuals, 0, Role.dad)

    def test_mother_role_is_correctly_set(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 4

        assert_role_at_index(individuals, 1, Role.mom)

    def test_proband_role_is_correctly_set(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 4

        assert_role_at_index(individuals, 2, Role.prb)

    def test_sibling_role_is_correctly_set(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 4

        assert_role_at_index(individuals, 3, Role.sib)


class TestMissingProbandFamily(BaseFamily):

    FAMILY_ID = 'nuclear_no_proband'

    def test_raises(self, family_pedigree, ped2family):
        with pytest.raises(NoProband):
            ped2family.to_family(self.family_members(family_pedigree))

    def test_family_is_skipped(self, family_pedigree, ped2family):
        families = ped2family.build_families(family_pedigree)
        assert "family1" not in families


class TestMissingFatherFamily(BaseFamily):

    FAMILY_ID = 'nuclear_no_father'

    def test_passes(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 3
        for individual in individuals:
            assert individual.individual.role != Role.unknown

    def test_sibling_with_unknown_father_is_maternal_half_sibling(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 3

        assert_role_at_index(individuals, 2, Role.maternal_half_sibling)


class TestMissingMotherFamily(BaseFamily):

    FAMILY_ID = 'nuclear_no_mother'

    def test_passes(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 3
        for individual in individuals:
            assert individual.individual.role != Role.unknown

    def test_sibling_with_unknown_mother_is_paternal_half_sibling(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == 3

        assert_role_at_index(individuals, 2, Role.paternal_half_sibling)


class TestExtendedFamily(BaseFamily):

    FAMILY_ID = 'extended'

    EXTENDED_FAMILY_COUNT = 21

    def test_all_have_roles(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))
        for individual in individuals:
            assert individual.individual.role != Role.unknown

    def test_stepmom_assigned_correctly(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 4, Role.step_mom)

    def test_maternal_half_sibling_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 5, Role.maternal_half_sibling)

    def test_stepdad_assigned_correctly(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 6, Role.step_dad)

    def test_paternal_half_sibling_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 7, Role.paternal_half_sibling)

    def test_paternal_grandfather_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 8, Role.paternal_grandfather)

    def test_paternal_grandmother_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 9, Role.paternal_grandmother)

    def test_maternal_grandfather_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 10, Role.maternal_grandfather)

    def test_maternal_grandmother_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 11, Role.maternal_grandmother)

    def test_maternal_uncle_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 12, Role.maternal_uncle)

    def test_maternal_aunt_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 13, Role.maternal_aunt)

    def test_paternal_uncle_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 14, Role.paternal_uncle)

    def test_paternal_aunt_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 15, Role.paternal_aunt)

    def test_paternal_cousins_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 16, Role.paternal_cousin)
        assert_role_at_index(individuals, 17, Role.paternal_cousin)

    def test_maternal_cousins_assigned_correctly(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))

        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 18, Role.maternal_cousin)
        assert_role_at_index(individuals, 19, Role.maternal_cousin)

    def test_child_assigned_correctly(self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))
        assert len(individuals) == TestExtendedFamily.EXTENDED_FAMILY_COUNT

        assert_role_at_index(individuals, 20, Role.child)


class TestFamilyWithOutsider(BaseFamily):

    FAMILY_ID = 'nuclear_with_outsider'

    def test_outsider_is_left_with_unknown_role(
            self, family_pedigree, ped2family):
        individuals = ped2family.to_family(
            self.family_members(family_pedigree))
        assert len(individuals) == 5
        assert len(
            [i for i in individuals if i.individual.role == Role.unknown]) == 1

        assert_role_at_index(individuals, 4, Role.unknown)


def test_nuclear_simple(family_pedigree):
    assert family_pedigree is not None
    assert isinstance(family_pedigree, defaultdict)

    families_builder = PedigreeToFamily()
    families = families_builder.build_families(family_pedigree)
    assert families is not None

    assert 'nuclear' in families
    members = families['nuclear']
    assert len(members) == 4

    m = members[0]
    assert m.get_individual_id() == 'dad'
    assert m.get_role() == Role.dad.name
    assert m.get_sex() == Sex.male.value
    assert m.get_status() == Status.unaffected.value

    m = members[1]
    assert m.get_individual_id() == 'mom'
    assert m.get_role() == Role.mom.name
    assert m.get_sex() == Sex.female.value
    assert m.get_status() == Status.unaffected.value

    m = members[2]
    assert m.get_individual_id() == 'prb'
    assert m.get_role() == Role.prb.name
    assert m.get_sex() == Sex.male.value
    assert m.get_status() == Status.affected.value

    m = members[3]
    assert m.get_individual_id() == 'sib'
    assert m.get_role() == Role.sib.name
    assert m.get_sex() == Sex.female.value
    assert m.get_status() == Status.unaffected.value


def test_nuclear_no_unknown_roles(family_pedigree):
    assert family_pedigree is not None
    assert isinstance(family_pedigree, defaultdict)

    families_builder = PedigreeToFamily()
    families = families_builder.build_families(family_pedigree)
    assert families is not None

    unknown = []
    for p in itertools.chain(*list(families.values())):
        if p.get_role() == "UNKNOWN":
            unknown.append(p)
            print((
                p.get_individual_id(), p.get_role(),
                p.get_sex(), p.get_status()))
    assert len(unknown) == 0
