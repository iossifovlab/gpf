"""Family members' roles with respect to the proband."""

import logging
from collections import defaultdict

from dae.pedigrees.family import Family, Person
from dae.variants.attributes import Role, Sex, Status

logger = logging.getLogger(__name__)


class Mating:
    """Class to represent a mating unit."""

    def __init__(self, mom_id: str, dad_id: str | None) -> None:
        self.mom_id = mom_id
        self.dad_id = dad_id
        self.mating_id = Mating.build_id(mom_id, dad_id)
        self.children: set[str] = set()

    @staticmethod
    def build_id(mom_id: str | None, dad_id: str | None) -> str:
        return f"{mom_id},{dad_id}"

    @staticmethod
    def parents_id(person: Person) -> str:
        assert person.mom_id is None or isinstance(person.mom_id, str), person
        assert person.dad_id is None or isinstance(person.dad_id, str), person

        return Mating.build_id(person.mom_id, person.dad_id)

    def __repr__(self) -> str:
        return f"({self.mating_id}> Mom: {self.mom_id}, Dad: {self.dad_id})"


class FamilyRoleBuilder:  # pylint: disable=too-few-public-methods
    """Build roles of family members."""

    def __init__(self, family: Family) -> None:
        self.family = family
        self.family_matings = self._build_family_matings()
        self.members_matings = self._build_members_matings()

    def build_roles(self) -> None:
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

    def _set_person_role(self, person: Person, role: Role) -> None:
        assert isinstance(person, Person)
        assert isinstance(role, Role)
        if (person.role is None or person.role == Role.unknown) and \
                role != person.role:
            logger.info(
                "changing role for %s from %s to %s",
                person, person.role, role)
            # pylint: disable=protected-access
            person._role = role  # noqa: SLF001
            person._attributes["role"] = role  # noqa: SLF001

    def _get_family_proband(self) -> Person | None:
        probands = self.family.get_members_with_roles([Role.prb])
        if len(probands) > 0:
            return probands[0]
        for person in self.family.full_members:
            is_proband = person.get_attr("proband", default=False)
            if is_proband:
                return person

        affected = self.family.get_members_with_statuses([Status.affected])
        affected = [
            p for p in affected
            if self.family.member_has_parent(p.person_id, allow_missing=True)]

        if len(affected) > 0:
            return affected[0]
        return None

    def _build_family_matings(self) -> dict[str, Mating]:
        matings = {}

        for person_id, person in self.family.persons.items():
            if self.family.member_has_parent(
                    person.person_id, allow_missing=True):

                parents_mating_id = Mating.parents_id(person)
                if parents_mating_id not in matings:
                    parents = Mating(person.mom_id, person.dad_id)
                    matings[parents_mating_id] = parents
                parents_mating = matings.get(parents_mating_id)
                assert parents_mating is not None
                parents_mating.children.add(person_id)
        return matings

    def _build_members_matings(self) -> dict[str, set[str]]:
        members_matings = defaultdict(set)
        for mating_id, mating in self.family_matings.items():
            if mating.mom_id is not None:
                members_matings[mating.mom_id].add(mating_id)
            if mating.dad_id is not None:
                members_matings[mating.dad_id].add(mating_id)
        return members_matings

    def _assign_roles_children(self, proband: Person) -> None:
        for mating_id in self.members_matings[proband.person_id]:
            mating = self.family_matings[mating_id]
            for child_id in mating.children:
                child = self.family.persons[child_id]
                self._set_person_role(child, Role.child)

    def _assign_roles_mates(self, proband: Person) -> None:
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

    def _assign_roles_parents(self, proband: Person) -> None:
        if not self.family.member_has_parent(
                proband.person_id, allow_missing=True):
            return
        mom = self.family.persons.get(proband.mom_id)
        if mom is not None:
            self._set_person_role(mom, Role.mom)
        dad = self.family.persons.get(proband.dad_id)
        if dad is not None:
            self._set_person_role(dad, Role.dad)

    def _assign_roles_siblings(self, proband: Person) -> None:
        if not self.family.member_has_parent(
                proband.person_id, allow_missing=True):
            return
        parents_mating = self.family_matings[Mating.parents_id(proband)]
        for person_id in parents_mating.children:
            if person_id != proband.person_id:
                person = self.family.persons[person_id]
                self._set_person_role(person, Role.sib)

    def _assign_roles_paternal(self, proband: Person) -> None:
        if not self.family.member_has_dad(
                proband.person_id, allow_missing=True):
            return
        dad = self.family.persons[proband.dad_id]
        if not self.family.member_has_parent(
                dad.person_id, allow_missing=True):
            return

        gd = self.family.persons.get(dad.dad_id)
        if gd is not None:
            self._set_person_role(gd, Role.paternal_grandfather)
        gm = self.family.persons.get(dad.mom_id)
        if gm is not None:
            self._set_person_role(gm, Role.paternal_grandmother)

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

    def _assign_roles_maternal(self, proband: Person) -> None:
        if not self.family.member_has_mom(
                proband.person_id, allow_missing=True):
            return
        mom = self.family.persons[proband.mom_id]
        if not self.family.member_has_parent(
                mom.person_id, allow_missing=True):
            return

        gd = self.family.persons.get(mom.dad_id)
        if gd is not None:
            self._set_person_role(gd, Role.maternal_grandfather)
        gm = self.family.persons.get(mom.mom_id)
        if gm is not None:
            self._set_person_role(gm, Role.maternal_grandmother)

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

    def _find_parent_matings(self, parent: Person) -> list[Mating]:
        matings = []
        for mating in self.family_matings.values():
            if parent.sex == Sex.male:
                if mating.dad_id == parent.person_id:
                    matings.append(mating)
            else:
                if mating.mom_id == parent.person_id:
                    matings.append(mating)

        return matings

    def _assign_roles_step_parents_and_half_siblings(
        self, proband: Person,
    ) -> None:
        if not self.family.member_has_parent(
                proband.person_id, allow_missing=True):
            return
        mom = self.family.persons.get(proband.mom_id)
        if mom is not None:
            mom_mates = filter(
                lambda x: x.dad_id != proband.dad_id,
                self._find_parent_matings(mom),
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
                        halfsibling, Role.maternal_half_sibling,
                    )
        dad = self.family.persons.get(proband.dad_id)
        if dad is not None:
            dad_mates = filter(
                lambda x: x.mom_id != proband.mom_id,
                self._find_parent_matings(dad),
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
                        halfsibling, Role.paternal_half_sibling,
                    )

    def _assign_unknown_roles(self) -> None:
        for person in self.family.persons.values():
            if person.role is None:
                self._set_person_role(person, Role.unknown)
