"""Helper class for tagging families."""

from typing import Optional

from dae.variants.attributes import Role, Status
from dae.pedigrees.family import Person, Family


class FamilyTagsBuilder:
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
