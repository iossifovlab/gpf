"""Family members' roles with respect to the proband."""

import logging

from collections import defaultdict

from dae.variants.attributes import Role, Status, Sex
from dae.pedigrees.family import Person


logger = logging.getLogger(__name__)


class Mating:
    """Class to represent a mating unit."""

    def __init__(self, mom_id, dad_id):
        self.mom_id = mom_id
        self.dad_id = dad_id
        self.mating_id = Mating.build_id(mom_id, dad_id)
        self.children = set()

    @staticmethod
    def build_id(mom_id, dad_id):
        return f"{mom_id},{dad_id}"

    @staticmethod
    def parents_id(person):
        assert person.mom_id is None or isinstance(person.mom_id, str), person
        assert person.dad_id is None or isinstance(person.dad_id, str), person

        return Mating.build_id(person.mom_id, person.dad_id)

    def __repr__(self):
        return f"({self.mating_id}> Mom: {self.mom_id}, Dad: {self.dad_id})"


class FamilyRoleBuilder:  # pylint: disable=too-few-public-methods
    """Build roles of family members."""

    def __init__(self, family):
        self.family = family
        self.family_matings = self._build_family_matings()
        self.members_matings = self._build_members_matings()

    def build_roles(self):
        """Build roles of all family members."""
        proband = self._get_family_proband()
        if proband is None:
            self._assign_unknown_roles()
            return

        assert proband is not None
        self._set_person_role(proband, Role.prb)

        self._assign_roles_children(proband)
        self._assign_roles_mates(proband)
        self._assign_roles_parents(proband)
        self._assign_roles_siblings(proband)
        self._assign_roles_paternal(proband)
        self._assign_roles_maternal(proband)
        self._assign_roles_step_parents_and_half_siblings(proband)
        self._assign_unknown_roles()

    @classmethod
    def _set_person_role(cls, person, role):
        assert isinstance(person, Person)
        assert isinstance(role, Role)
        if person.role is None or person.role == Role.unknown:
            if role != person.role:
                logger.info(
                    "changing role for %s from %s to %s",
                    person, person.role, role)
                # pylint: disable=protected-access
                person._role = role
                person._attributes["role"] = role

    def _get_family_proband(self):
        probands = self.family.get_members_with_roles([Role.prb])
        if len(probands) > 0:
            return probands[0]
        for person in self.family.full_members:
            is_proband = person.get_attr("proband", False)
            # assert isinstance(is_proband, bool), is_proband
            if is_proband:
                return person

        affected = self.family.get_members_with_statuses([Status.affected])
        affected = [p for p in affected if p.has_parent()]

        if len(affected) > 0:
            return affected[0]
        return None

    def _build_family_matings(self):
        matings = {}

        for person_id, person in self.family.persons.items():
            if person.has_parent():

                parents_mating_id = Mating.parents_id(person)
                if parents_mating_id not in matings:
                    parents = Mating(person.mom_id, person.dad_id)
                    matings[parents_mating_id] = parents
                parents_mating = matings.get(parents_mating_id)
                assert parents_mating is not None
                parents_mating.children.add(person_id)
        return matings

    def _build_members_matings(self):
        members_matings = defaultdict(set)
        for mating_id, mating in self.family_matings.items():
            if mating.mom_id is not None:
                members_matings[mating.mom_id].add(mating_id)
            if mating.dad_id is not None:
                members_matings[mating.dad_id].add(mating_id)
        return members_matings

    def _assign_roles_children(self, proband):
        for mating_id in self.members_matings[proband.person_id]:
            mating = self.family_matings[mating_id]
            for child_id in mating.children:
                child = self.family.persons[child_id]
                self._set_person_role(child, Role.child)

    def _assign_roles_mates(self, proband):
        for mating_id in self.members_matings[proband.person_id]:
            mating = self.family_matings[mating_id]
            if (
                mating.dad_id is not None
                and mating.dad_id != proband.person_id
            ):
                person = self.family.persons[mating.dad_id]
                self._set_person_role(person, Role.spouse)
            elif mating.mom_id is not None and \
                    mating.mom_id != proband.person_id:
                person = self.family.persons[mating.mom_id]
                self._set_person_role(person, Role.spouse)

    def _assign_roles_parents(self, proband):
        if not proband.has_parent():
            return
        if proband.mom is not None:
            self._set_person_role(proband.mom, Role.mom)
        if proband.dad is not None:
            self._set_person_role(proband.dad, Role.dad)

    def _assign_roles_siblings(self, proband):
        if not proband.has_parent():
            return
        parents_mating = self.family_matings[Mating.parents_id(proband)]
        for person_id in parents_mating.children:
            if person_id != proband.person_id:
                person = self.family.persons[person_id]
                self._set_person_role(person, Role.sib)

    def _assign_roles_paternal(self, proband):
        if proband.dad is None or not proband.dad.has_parent():
            return

        dad = proband.dad
        if dad.dad is not None:
            self._set_person_role(dad.dad, Role.paternal_grandfather)
        if dad.mom is not None:
            self._set_person_role(dad.mom, Role.paternal_grandmother)

        grandparents_mating_id = Mating.parents_id(dad)
        grandparents_mating = self.family_matings[grandparents_mating_id]
        for person_id in grandparents_mating.children:
            person = self.family.persons[person_id]
            if person.role is not None and person.role != Role.unknown:
                continue
            if person.sex == Sex.M:
                self._set_person_role(person, Role.paternal_uncle)
            if person.sex == Sex.F:
                self._set_person_role(person, Role.paternal_aunt)

            for person_mating_id in self.members_matings[person.person_id]:
                person_mating = self.family_matings[person_mating_id]
                for cousin_id in person_mating.children:
                    cousin = self.family.persons[cousin_id]
                    self._set_person_role(cousin, Role.paternal_cousin)

    def _assign_roles_maternal(self, proband):
        if proband.mom is None or not proband.mom.has_parent():
            return

        mom = proband.mom
        if mom.dad is not None:
            self._set_person_role(mom.dad, Role.maternal_grandfather)
        if mom.mom is not None:
            self._set_person_role(mom.mom, Role.maternal_grandmother)

        grandparents_mating_id = Mating.parents_id(mom)
        grandparents_mating = self.family_matings[grandparents_mating_id]
        for person_id in grandparents_mating.children:
            person = self.family.persons[person_id]
            if person.role is not None and person.role != Role.unknown:
                continue
            if person.sex == Sex.M:
                self._set_person_role(person, Role.maternal_uncle)
            if person.sex == Sex.F:
                self._set_person_role(person, Role.maternal_aunt)

            for person_mating_id in self.members_matings[person.person_id]:
                person_mating = self.family_matings[person_mating_id]
                for cousin_id in person_mating.children:
                    cousin = self.family.persons[cousin_id]
                    self._set_person_role(cousin, Role.maternal_cousin)

    def _find_parent_matings(self, parent):
        matings = []
        for mating in self.family_matings.values():
            if parent.sex == Sex.male:
                if mating.dad_id == parent.person_id:
                    matings.append(mating)
            else:
                if mating.mom_id == parent.person_id:
                    matings.append(mating)

        return matings

    def _assign_roles_step_parents_and_half_siblings(self, proband):
        if proband.mom is None or proband.dad is None:
            return
        if proband.mom is not None:
            mom_mates = filter(
                lambda x: x.dad_id != proband.dad.person_id,
                self._find_parent_matings(proband.mom),
            )
            for mating in mom_mates:
                if mating.dad_id is None:
                    continue
                step_dad = self.family.persons[mating.dad_id]
                self._set_person_role(step_dad, Role.step_dad)
                maternal_halfsiblings_ids = mating.children
                for halfsibling_id in maternal_halfsiblings_ids:
                    halfsibling = self.family.persons[halfsibling_id]
                    self._set_person_role(
                        halfsibling, Role.maternal_half_sibling
                    )
        if proband.dad is not None:
            dad_mates = filter(
                lambda x: x.mom_id != proband.mom.person_id,
                self._find_parent_matings(proband.dad),
            )
            for mating in dad_mates:
                if mating.mom_id is None:
                    continue
                step_mom = self.family.persons[mating.mom_id]
                self._set_person_role(step_mom, Role.step_mom)
                paternal_halfsiblings_ids = mating.children
                for halfsibling_id in paternal_halfsiblings_ids:
                    halfsibling = self.family.persons[halfsibling_id]
                    self._set_person_role(
                        halfsibling, Role.paternal_half_sibling
                    )

    def _assign_unknown_roles(self):
        for person in self.family.persons.values():
            if person.role is None:
                self._set_person_role(person, Role.unknown)
