import pytest
import enum
import sys

from dae.pheno.prepare.individuals2ped import FamilyToPedigree
from dae.pheno.tests.test_ped2individuals import BaseFamily


@pytest.fixture(scope="module")
def family2ped():
    return FamilyToPedigree()


def assert_mother_father_by_individual_id(
    members, individual_id, mother_id, father_id
):
    current_individuals = [
        member
        for member in members
        if member.get_individual_id() == individual_id.value
    ]

    assert len(current_individuals) == 1

    member = current_individuals[0]
    assert member.get_father_id() == father_id.value
    assert member.get_mother_id() == mother_id.value


class FamilyIds(enum.Enum):
    NO_ONE = "0"
    MOM = "mom"
    DAD = "dad"
    PRB = "prb"
    SIB = "sib"
    OUTSIDER = "outsider"

    STEPFATHER = "stepdad"
    STEPMOM = "stepmom"

    MATERNAL_UNCLE = "m_uncle"
    MATERNAL_AUNT = "m_aunt"
    MATERNAL_COUSIN1 = "m_cousin1"
    MATERNAL_COUSIN2 = "m_cousin2"
    MATERNAL_GRANDFATHER = "m_grandad"
    MATERNAL_GRANDMOTHER = "m_grandmom"
    MATERNAL_HALF_SIBLING = "mh_sibling"

    PATERNAL_UNCLE = "p_uncle"
    PATERNAL_AUNT = "p_aunt"
    PATERNAL_COUSIN1 = "p_cousin1"
    PATERNAL_COUSIN2 = "p_cousin2"
    PATERNAL_GRANDFATHER = "p_grandad"
    PATERNAL_GRANDMOTHER = "p_grandmom"
    PATERNAL_HALF_SIBLING = "ph_sibling"


def to_id(relation):
    ids = to_tuple(relation[0], relation[1])
    ids = [x.value for x in ids]
    return "{}->{};{}".format(*ids)


def to_names(relations):
    return list(map(to_id, relations))


def to_tuple(individual, mom_and_dad):
    return individual, mom_and_dad[0], mom_and_dad[1]


def to_tuples(rels):
    return [to_tuple(x[0], x[1]) for x in rels]


class BaseIndividuals2PedFamily(BaseFamily):
    def test_relations(self, relations_to_test, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert_mother_father_by_individual_id(
            members,
            relations_to_test[0],
            relations_to_test[1],
            relations_to_test[2],
        )


class TestNuclearFamily(BaseIndividuals2PedFamily):

    FAMILY_ID = "nuclear"
    SIMPLE_RELATIONS_TO_TEST = {
        FamilyIds.DAD: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.MOM: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PRB: [FamilyIds.MOM, FamilyIds.DAD],
        FamilyIds.SIB: [FamilyIds.MOM, FamilyIds.DAD],
    }

    @pytest.fixture(
        params=to_tuples(list(SIMPLE_RELATIONS_TO_TEST.items())),
        ids=to_names(list(SIMPLE_RELATIONS_TO_TEST.items())),
    )
    def relations_to_test(self, request):
        return request.param

    def test_passes(self, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert len(members) == 4


class TestNuclearFamilyWithoutFather(BaseIndividuals2PedFamily):

    FAMILY_ID = "nuclear_no_father"
    SIMPLE_RELATIONS_TO_TEST = {
        FamilyIds.MOM: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PRB: [FamilyIds.MOM, FamilyIds.NO_ONE],
        FamilyIds.SIB: [FamilyIds.MOM, FamilyIds.NO_ONE],
    }

    @pytest.fixture(
        params=to_tuples(list(SIMPLE_RELATIONS_TO_TEST.items())),
        ids=to_names(list(SIMPLE_RELATIONS_TO_TEST.items())),
    )
    def relations_to_test(self, request):
        return request.param

    def test_passes(self, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert len(members) == 3


class TestNuclearFamilyWithoutMother(BaseIndividuals2PedFamily):

    FAMILY_ID = "nuclear_no_mother"
    SIMPLE_RELATIONS_TO_TEST = {
        FamilyIds.DAD: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PRB: [FamilyIds.NO_ONE, FamilyIds.DAD],
        FamilyIds.SIB: [FamilyIds.NO_ONE, FamilyIds.DAD],
    }

    @pytest.fixture(
        params=to_tuples(list(SIMPLE_RELATIONS_TO_TEST.items())),
        ids=to_names(list(SIMPLE_RELATIONS_TO_TEST.items())),
    )
    def relations_to_test(self, request):
        return request.param

    def test_passes(self, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert len(members) == 3


class TestNuclearFamilyWithoutProband(BaseIndividuals2PedFamily):

    FAMILY_ID = "nuclear_no_proband"
    SIMPLE_RELATIONS_TO_TEST = {
        FamilyIds.DAD: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.MOM: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.SIB: [FamilyIds.MOM, FamilyIds.DAD],
    }

    @pytest.fixture(
        params=to_tuples(list(SIMPLE_RELATIONS_TO_TEST.items())),
        ids=to_names(list(SIMPLE_RELATIONS_TO_TEST.items())),
    )
    def relations_to_test(self, request):
        return request.param

    def test_passes(self, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert len(members) == 3


class TestExtendedFamily(BaseIndividuals2PedFamily):

    FAMILY_ID = "extended"
    EXTENDED_FAMILY_COUNT = 20
    EXTENDED_FAMILY_AMBIGUOUS_COUNT = 6
    SIMPLE_RELATIONS_TO_TEST = {
        FamilyIds.DAD: [
            FamilyIds.PATERNAL_GRANDMOTHER,
            FamilyIds.PATERNAL_GRANDFATHER,
        ],
        FamilyIds.MOM: [
            FamilyIds.MATERNAL_GRANDMOTHER,
            FamilyIds.MATERNAL_GRANDFATHER,
        ],
        FamilyIds.SIB: [FamilyIds.MOM, FamilyIds.DAD],
        FamilyIds.PRB: [FamilyIds.MOM, FamilyIds.DAD],
        FamilyIds.STEPFATHER: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.STEPMOM: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PATERNAL_GRANDFATHER: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PATERNAL_GRANDMOTHER: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PATERNAL_HALF_SIBLING: [FamilyIds.NO_ONE, FamilyIds.DAD],
        FamilyIds.PATERNAL_COUSIN1: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PATERNAL_COUSIN2: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.PATERNAL_AUNT: [
            FamilyIds.PATERNAL_GRANDMOTHER,
            FamilyIds.PATERNAL_GRANDFATHER,
        ],
        FamilyIds.PATERNAL_UNCLE: [
            FamilyIds.PATERNAL_GRANDMOTHER,
            FamilyIds.PATERNAL_GRANDFATHER,
        ],
        FamilyIds.MATERNAL_GRANDFATHER: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.MATERNAL_GRANDMOTHER: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.MATERNAL_HALF_SIBLING: [FamilyIds.MOM, FamilyIds.NO_ONE],
        FamilyIds.MATERNAL_COUSIN1: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.MATERNAL_COUSIN2: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
        FamilyIds.MATERNAL_AUNT: [
            FamilyIds.MATERNAL_GRANDMOTHER,
            FamilyIds.MATERNAL_GRANDFATHER,
        ],
        FamilyIds.MATERNAL_UNCLE: [
            FamilyIds.MATERNAL_GRANDMOTHER,
            FamilyIds.MATERNAL_GRANDFATHER,
        ],
    }

    @pytest.fixture(
        params=to_tuples(list(SIMPLE_RELATIONS_TO_TEST.items())),
        ids=to_names(list(SIMPLE_RELATIONS_TO_TEST.items())),
    )
    def relations_to_test(self, request):
        return request.param

    def test_passes(self, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert len(members) == self.EXTENDED_FAMILY_COUNT

    def test_ambiguous_roles_give_warning(
        self, family_roles, family2ped, mocker
    ):

        mock_stderr = mocker.patch.object(sys, "stderr", autospec=True)
        family2ped.to_pedigree(self.family_members(family_roles))

        assert (
            mock_stderr.write.call_count
            == self.EXTENDED_FAMILY_AMBIGUOUS_COUNT
        )

        errors = mock_stderr.write.call_args_list
        assert len(errors) == self.EXTENDED_FAMILY_AMBIGUOUS_COUNT
        for line in errors:
            assert "ambiguous role" in line[0][0]

        for role in FamilyToPedigree.AMBIGUOUS_ROLES:
            assert next(
                (line for line in errors if str(role) in line[0][0]), None
            )


class TestGrandmotherOnlyFamily(BaseFamily):

    FAMILY_ID = "only_grandmother"

    def test_passes(self, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert len(members) == 1


class TestNuclearFamilyWithOutsider(BaseIndividuals2PedFamily):

    FAMILY_ID = "nuclear_with_unknown"
    SIMPLE_RELATIONS_TO_TEST = {
        FamilyIds.OUTSIDER: [FamilyIds.NO_ONE, FamilyIds.NO_ONE],
    }

    @pytest.fixture(
        params=to_tuples(list(SIMPLE_RELATIONS_TO_TEST.items())),
        ids=to_names(list(SIMPLE_RELATIONS_TO_TEST.items())),
    )
    def relations_to_test(self, request):
        return request.param

    def test_passes(self, family_roles, family2ped):
        members = family2ped.to_pedigree(self.family_members(family_roles))

        assert len(members) == 5
