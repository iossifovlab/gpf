"""Helper class for tagging families."""

from typing import Iterable, Optional

from dae.variants.attributes import Role, Status, Sex
from dae.pedigrees.family import Person, Family


class FamilyTagBuilder:  # pylint: disable=too-many-public-methods
    """Tag families with a series of predefined tags."""

    def __init__(self, family: Family):
        self.family = family

    def get_mom(self) -> Optional[Person]:
        for person in self.family.members_in_order:
            if person.role == Role.mom:
                return person
        return None

    def get_dad(self) -> Optional[Person]:
        for person in self.family.members_in_order:
            if person.role == Role.dad:
                return person
        return None

    def get_prb(self) -> Optional[Person]:
        for person in self.family.members_in_order:
            if person.role == Role.prb:
                return person
        return None

    def get_sibs(self) -> Iterable[Person]:
        result = []
        for person in self.family.members_in_order:
            if person.role == Role.sib:
                result.append(person)
        return result

    def tag(self, label, value) -> None:
        for person in self.family.persons.values():
            person.set_attr(label, value)

    def check_tag(self, label, value) -> bool:
        for person in self.family.persons.values():
            if not person.has_attr(label):
                raise ValueError(f"preson has no attributes {label}")
            if person.get_attr(label) != value:
                return False
        return True

    def check_nuclear_family(self) -> bool:
        """Check if the family is a nuclear family."""
        mom = self.get_mom()
        dad = self.get_dad()

        if mom is None or dad is None:
            return False

        for person in self.family.persons.values():
            if person.person_id in {mom.person_id, dad.person_id}:
                continue

            if not person.has_both_parents():
                return False
            if person.mom_id != mom.person_id \
                    or person.dad_id != dad.person_id:
                return False

        return True

    def tag_nuclear_family(self) -> bool:
        """Set nuclear family tag to the family."""
        value = self.check_nuclear_family()
        self.tag("tag_nuclear_family", value)
        return value

    def check_quad_family(self) -> bool:
        if len(self.family) != 4:
            return False
        if not self.check_nuclear_family():
            return False

        return True

    def tag_quad_family(self) -> bool:
        """Set quad family tag to the family."""
        value = self.check_quad_family()
        self.tag("tag_quad_family", value)
        return value

    def check_trio_family(self) -> bool:
        if len(self.family) != 3:
            return False
        if not self.check_nuclear_family():
            return False

        return True

    def tag_trio_family(self) -> bool:
        """Set trio family tag to the family."""
        value = self.check_trio_family()
        self.tag("tag_trio_family", value)
        return value

    def check_simplex_family(self) -> bool:
        return len(list(filter(
            lambda p: p.status == Status.affected,
            self.family.persons.values()))) == 1

    def tag_simplex_family(self) -> bool:
        """Set simplex family tag to the family."""
        value = self.check_simplex_family()
        self.tag("tag_simplex_family", value)
        return value

    def check_multiplex_family(self) -> bool:
        return len(list(filter(
            lambda p: p.status == Status.affected,
            self.family.persons.values()))) > 1

    def tag_multiplex_family(self) -> bool:
        """Set multiplex family tag to the family."""
        value = self.check_multiplex_family()
        self.tag("tag_multiplex_family", value)
        return value

    def check_control_family(self) -> bool:
        return len(list(filter(
            lambda p: p.status == Status.affected,
            self.family.persons.values()))) == 0

    def tag_control_family(self) -> bool:
        """Set control family tag to the family."""
        value = self.check_control_family()
        self.tag("tag_control_family", value)
        return value

    def check_affected_dad_family(self) -> bool:
        dad = self.get_dad()
        if dad is None:
            return False
        return bool(dad.status == Status.affected)

    def tag_affected_dad_family(self) -> bool:
        """Set affected dad family tag to the family."""
        value = self.check_affected_dad_family()
        self.tag("tag_affected_dad_family", value)
        return value

    def check_affected_mom_family(self) -> bool:
        mom = self.get_mom()
        if mom is None:
            return False
        return bool(mom.status == Status.affected)

    def tag_affected_mom_family(self) -> bool:
        """Set affected mom family tag to the family."""
        value = self.check_affected_mom_family()
        self.tag("tag_affected_mom_family", value)
        return value

    def check_affected_prb_family(self) -> bool:
        prb = self.get_prb()
        if prb is None:
            return False
        return bool(prb.status == Status.affected)

    def tag_affected_prb_family(self) -> bool:
        """Set affected proband family tag to the family."""
        value = self.check_affected_prb_family()
        self.tag("tag_affected_prb_family", value)
        return value

    def check_affected_sib_family(self) -> bool:
        for sib in self.get_sibs():
            if sib.status == Status.affected:
                return True
        return False

    def tag_affected_sib_family(self) -> bool:
        """Set affected sibling family tag to the family."""
        value = self.check_affected_sib_family()
        self.tag("tag_affected_sib_family", value)
        return value

    def check_male_prb_family(self) -> bool:
        prb = self.get_prb()
        if prb is None:
            return False
        return bool(prb.sex == Sex.male)

    def tag_male_prb_family(self) -> bool:
        """Set male proband family tag to the family."""
        value = self.check_male_prb_family()
        self.tag("tag_male_prb_family", value)
        return value

    def check_female_prb_family(self) -> bool:
        prb = self.get_prb()
        if prb is None:
            return False
        return bool(prb.sex == Sex.female)

    def tag_female_prb_family(self) -> bool:
        """Set female proband family tag to the family."""
        value = self.check_female_prb_family()
        self.tag("tag_female_prb_family", value)
        return value

    def check_missing_mom_family(self) -> bool:
        if self.get_mom() is None:
            return True
        return False

    def tag_missing_mom_family(self) -> bool:
        """Set missing mom family tag to the family."""
        value = self.check_missing_mom_family()
        self.tag("tag_missing_mom_family", value)
        return value

    def check_missing_dad_family(self) -> bool:
        if self.get_dad() is None:
            return True
        return False

    def tag_missing_dad_family(self) -> bool:
        """Set missing dad family tag to the family."""
        value = self.check_missing_dad_family()
        self.tag("tag_missing_dad_family", value)
        return value