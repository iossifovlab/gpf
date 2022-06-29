"""Helper class for tagging families."""

from typing import Callable, Iterable, Optional, Dict

from dae.variants.attributes import Role, Status, Sex
from dae.pedigrees.family import FamiliesData, Person, Family



def _get_mom(family: Family) -> Optional[Person]:
    for person in family.members_in_order:
        if person.role == Role.mom:
            return person
    return None

def _get_dad(family: Family) -> Optional[Person]:
    for person in family.members_in_order:
        if person.role == Role.dad:
            return person
    return None

def _get_prb(family: Family) -> Optional[Person]:
    for person in family.members_in_order:
        if person.role == Role.prb:
            return person
    return None

def _get_sibs(family: Family) -> Iterable[Person]:
    result = []
    for person in family.members_in_order:
        if person.role == Role.sib:
            result.append(person)
    return result

def _tag(family: Family, label: str, value) -> None:
    for person in family.persons.values():
        person.set_attr(label, value)

def check_tag(family: Family, label: str, value) -> bool:
    for person in family.persons.values():
        if not person.has_attr(label):
            raise ValueError(f"preson has no attributes {label}")
        if person.get_attr(label) != value:
            return False
    return True


def check_nuclear_family(family: Family) -> bool:
    """Check if the family is a nuclear family."""
    mom = _get_mom(family)
    dad = _get_dad(family)

    if mom is None or dad is None:
        return False

    for person in family.persons.values():
        if person.person_id in {mom.person_id, dad.person_id}:
            continue

        if not person.has_both_parents():
            return False
        if person.mom_id != mom.person_id \
                or person.dad_id != dad.person_id:
            return False

    return True


def tag_nuclear_family(family: Family) -> bool:
    """Set nuclear family tag to the family."""
    value = check_nuclear_family(family)
    _tag(family, "tag_nuclear_family", value)
    return value


def check_quad_family(family: Family) -> bool:
    if len(family) != 4:
        return False
    if not check_nuclear_family(family):
        return False

    return True


def tag_quad_family(family: Family) -> bool:
    """Set quad family tag to the family."""
    value = check_quad_family(family)
    _tag(family, "tag_quad_family", value)
    return value


def check_trio_family(family: Family) -> bool:
    if len(family) != 3:
        return False
    if not check_nuclear_family(family):
        return False

    return True


def tag_trio_family(family: Family) -> bool:
    """Set trio family tag to the family."""
    value = check_trio_family(family)
    _tag(family, "tag_trio_family", value)
    return value


def check_simplex_family(family: Family) -> bool:
    return len(list(filter(
        lambda p: p.status == Status.affected,
        family.persons.values()))) == 1


def tag_simplex_family(family: Family) -> bool:
    """Set simplex family tag to the family."""
    value = check_simplex_family(family)
    _tag(family, "tag_simplex_family", value)
    return value


def check_multiplex_family(family: Family) -> bool:
    return len(list(filter(
        lambda p: p.status == Status.affected,
        family.persons.values()))) > 1


def tag_multiplex_family(family: Family) -> bool:
    """Set multiplex family tag to the family."""
    value = check_multiplex_family(family)
    _tag(family, "tag_multiplex_family", value)
    return value


def check_control_family(family: Family) -> bool:
    return len(list(filter(
        lambda p: p.status == Status.affected,
        family.persons.values()))) == 0


def tag_control_family(family: Family) -> bool:
    """Set control family tag to the family."""
    value = check_control_family(family)
    _tag(family, "tag_control_family", value)
    return value


def check_affected_dad_family(family: Family) -> bool:
    dad = _get_dad(family)
    if dad is None:
        return False
    return bool(dad.status == Status.affected)


def tag_affected_dad_family(family: Family) -> bool:
    """Set affected dad family tag to the family."""
    value = check_affected_dad_family(family)
    _tag(family, "tag_affected_dad_family", value)
    return value


def check_affected_mom_family(family: Family) -> bool:
    mom = _get_mom(family)
    if mom is None:
        return False
    return bool(mom.status == Status.affected)


def tag_affected_mom_family(family: Family) -> bool:
    """Set affected mom family tag to the family."""
    value = check_affected_mom_family(family)
    _tag(family, "tag_affected_mom_family", value)
    return value


def check_affected_prb_family(family: Family) -> bool:
    prb = _get_prb(family)
    if prb is None:
        return False
    return bool(prb.status == Status.affected)


def tag_affected_prb_family(family: Family) -> bool:
    """Set affected proband family tag to the family."""
    value = check_affected_prb_family(family)
    _tag(family, "tag_affected_prb_family", value)
    return value


def check_affected_sib_family(family: Family) -> bool:
    for sib in _get_sibs(family):
        if sib.status == Status.affected:
            return True
    return False


def tag_affected_sib_family(family: Family) -> bool:
    """Set affected sibling family tag to the family."""
    value = check_affected_sib_family(family)
    _tag(family, "tag_affected_sib_family", value)
    return value


def check_male_prb_family(family: Family) -> bool:
    prb = _get_prb(family)
    if prb is None:
        return False
    return bool(prb.sex == Sex.male)


def tag_male_prb_family(family: Family) -> bool:
    """Set male proband family tag to the family."""
    value = check_male_prb_family(family)
    _tag(family, "tag_male_prb_family", value)
    return value


def check_female_prb_family(family: Family) -> bool:
    prb = _get_prb(family)
    if prb is None:
        return False
    return bool(prb.sex == Sex.female)


def tag_female_prb_family(family: Family) -> bool:
    """Set female proband family tag to the family."""
    value = check_female_prb_family(family)
    _tag(family, "tag_female_prb_family", value)
    return value


def check_missing_mom_family(family: Family) -> bool:
    if _get_mom(family) is None:
        return True
    return False


def tag_missing_mom_family(family: Family) -> bool:
    """Set missing mom family tag to the family."""
    value = check_missing_mom_family(family)
    _tag(family, "tag_missing_mom_family", value)
    return value


def check_missing_dad_family(family: Family) -> bool:
    if _get_dad(family) is None:
        return True
    return False


def tag_missing_dad_family(family: Family) -> bool:
    """Set missing dad family tag to the family."""
    value = check_missing_dad_family(family)
    _tag(family, "tag_missing_dad_family", value)
    return value


class FamilyTagsBuilder:
    """Class used ot apply all tags to a family."""

    TAGS: Dict[str, Callable[[Family], bool]] = {
        "tag_nuclear_family": tag_nuclear_family,
        "tag_quad_family": tag_quad_family,
        "tag_trio_family": tag_trio_family,
        "tag_simplex_family": tag_simplex_family,
        "tag_multiplex_family": tag_multiplex_family,
        "tag_control_family": tag_control_family,
        "tag_affected_dad_family": tag_affected_dad_family,
        "tag_affected_mom_family": tag_affected_mom_family,
        "tag_affected_prb_family": tag_affected_prb_family,
        "tag_affected_sib_family": tag_affected_sib_family,
        "tag_male_prb_family": tag_male_prb_family,
        "tag_female_prb_family": tag_female_prb_family,
        "tag_missing_mom_family": tag_missing_mom_family,
        "tag_missing_dad_family": tag_missing_dad_family,
    }
    def __init__(self):
        self._taggers = {}
        self._taggers.update(self.TAGS)

    def add_tagger(
            self, label: str,
            tagger: Callable[[Family], bool]) -> None:
        self._taggers[label] = tagger

    def tag_family(self, family: Family) -> None:
        """Tag family with all available tags."""
        family_tags = set()
        for label, tagger in self._taggers.items():
            value = tagger(family)
            if isinstance(value, bool):
                if value:
                    family_tags.add(label)
                continue

            family_tags.add(f"{label}:{value}")
        _tag(family, "tags", ";".join(sorted(family_tags)))

    def tag_families_data(self, families: FamiliesData):
        for family in families.values():
            self.tag_family(family)
