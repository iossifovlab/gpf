import logging

from dae.variants.attributes import Role, Sex


logger = logging.getLogger(__name__)


class FamilyStructureBuilder:
    def __init__(self, family):
        self.family = family

    def build_structure(self):
        self._set_structure_children()
        self.family.redefine()

    def _get_persons_with_role(self, roles):
        result = []
        for person in self.family.full_members:
            if person.role in roles:
                result.append(person)
        return result

    def _get_person_with_role(self, role):
        result = self._get_persons_with_role(set([role]))
        assert len(result) <= 1
        if result:
            return result[0]
        else:
            return None

    def _set_structure_children(self):
        children = self._get_persons_with_role(set([Role.prb, Role.sib]))
        mom = self._get_person_with_role(Role.mom)
        dad = self._get_person_with_role(Role.dad)

        if mom:
            assert mom.sex == Sex.F
        if dad:
            assert dad.sex == Sex.M

        for child in children:
            child._attributes["mom_id"] = \
                mom.person_id if mom is not None else None
            child._attributes["dad_id"] = \
                dad.person_id if dad is not None else None
            child.redefine()

    # def _assign_roles_mates(self, proband):
    #     for mating_id in self.members_matings[proband.person_id]:
    #         mating = self.family_matings[mating_id]
    #         if (
    #             mating.dad_id is not None
    #             and mating.dad_id != proband.person_id
    #         ):
    #             person = self.family.persons[mating.dad_id]
    #             self._set_person_role(person, Role.spouse)
    #         elif mating.mom_id is not None and \
    #                 mating.mom_id != proband.person_id:
    #             person = self.family.persons[mating.mom_id]
    #             self._set_person_role(person, Role.spouse)

    # def _assign_roles_parents(self, proband):
    #     if not proband.has_parent():
    #         return
    #     if proband.mom is not None:
    #         self._set_person_role(proband.mom, Role.mom)
    #     if proband.dad is not None:
    #         self._set_person_role(proband.dad, Role.dad)

    # def _assign_roles_siblings(self, proband):
    #     if not proband.has_parent():
    #         return
    #     parents_mating = self.family_matings[Mating.parents_id(proband)]
    #     for person_id in parents_mating.children:
    #         if person_id != proband.person_id:
    #             person = self.family.persons[person_id]
    #             self._set_person_role(person, Role.sib)

    # def _assign_roles_paternal(self, proband):
    #     if proband.dad is None or not proband.dad.has_parent():
    #         return

    #     dad = proband.dad
    #     if dad.dad is not None:
    #         self._set_person_role(dad.dad, Role.paternal_grandfather)
    #     if dad.mom is not None:
    #         self._set_person_role(dad.mom, Role.paternal_grandmother)

    #     grandparents_mating_id = Mating.parents_id(dad)
    #     grandparents_mating = self.family_matings[grandparents_mating_id]
    #     for person_id in grandparents_mating.children:
    #         person = self.family.persons[person_id]
    #         if person.role is not None and person.role != Role.unknown:
    #             continue
    #         if person.sex == Sex.M:
    #             self._set_person_role(person, Role.paternal_uncle)
    #         if person.sex == Sex.F:
    #             self._set_person_role(person, Role.paternal_aunt)

    #         for person_mating_id in self.members_matings[person.person_id]:
    #             person_mating = self.family_matings[person_mating_id]
    #             for cousin_id in person_mating.children:
    #                 cousin = self.family.persons[cousin_id]
    #                 self._set_person_role(cousin, Role.paternal_cousin)

    # def _assign_roles_maternal(self, proband):
    #     if proband.mom is None or not proband.mom.has_parent():
    #         return

    #     mom = proband.mom
    #     if mom.dad is not None:
    #         self._set_person_role(mom.dad, Role.maternal_grandfather)
    #     if mom.mom is not None:
    #         self._set_person_role(mom.mom, Role.maternal_grandmother)

    #     grandparents_mating_id = Mating.parents_id(mom)
    #     grandparents_mating = self.family_matings[grandparents_mating_id]
    #     for person_id in grandparents_mating.children:
    #         person = self.family.persons[person_id]
    #         if person.role is not None and person.role != Role.unknown:
    #             continue
    #         if person.sex == Sex.M:
    #             self._set_person_role(person, Role.maternal_uncle)
    #         if person.sex == Sex.F:
    #             self._set_person_role(person, Role.maternal_aunt)

    #         for person_mating_id in self.members_matings[person.person_id]:
    #             person_mating = self.family_matings[person_mating_id]
    #             for cousin_id in person_mating.children:
    #                 cousin = self.family.persons[cousin_id]
    #                 self._set_person_role(cousin, Role.maternal_cousin)

    # def _find_parent_matings(self, parent):
    #     matings = []
    #     for mating in self.family_matings.values():
    #         if parent.sex == Sex.male:
    #             if mating.dad_id == parent.person_id:
    #                 matings.append(mating)
    #         else:
    #             if mating.mom_id == parent.person_id:
    #                 matings.append(mating)

    #     return matings

    # def _assign_roles_step_parents_and_half_siblings(self, proband):
    #     if proband.mom is None or proband.dad is None:
    #         return
    #     if proband.mom is not None:
    #         mom_mates = filter(
    #             lambda x: x.dad_id != proband.dad.person_id,
    #             self._find_parent_matings(proband.mom),
    #         )
    #         for mating in mom_mates:
    #             if mating.dad_id is None:
    #                 continue
    #             step_dad = self.family.persons[mating.dad_id]
    #             self._set_person_role(step_dad, Role.step_dad)
    #             maternal_halfsiblings_ids = mating.children
    #             for halfsibling_id in maternal_halfsiblings_ids:
    #                 halfsibling = self.family.persons[halfsibling_id]
    #                 self._set_person_role(
    #                     halfsibling, Role.maternal_half_sibling
    #                 )
    #     if proband.dad is not None:
    #         dad_mates = filter(
    #             lambda x: x.mom_id != proband.mom.person_id,
    #             self._find_parent_matings(proband.dad),
    #         )
    #         for mating in dad_mates:
    #             if mating.mom_id is None:
    #                 continue
    #             step_mom = self.family.persons[mating.mom_id]
    #             self._set_person_role(step_mom, Role.step_mom)
    #             paternal_halfsiblings_ids = mating.children
    #             for halfsibling_id in paternal_halfsiblings_ids:
    #                 halfsibling = self.family.persons[halfsibling_id]
    #                 self._set_person_role(
    #                     halfsibling, Role.paternal_half_sibling
    #                 )

    # def _assign_unknown_roles(self):
    #     for person in self.family.persons.values():
    #         if person.role is None:
    #             self._set_person_role(person, Role.unknown)
