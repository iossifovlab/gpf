"""Helper class for tagging families."""
from typing import Callable, Iterable, Optional, Any
from collections import Counter

from dae.variants.attributes import Role, Status, Sex
from dae.pedigrees.family import FamiliesData, Person, Family, FamilyTag


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


def set_tag(family: Family, tag: FamilyTag) -> None:
    for person in family.persons.values():
        person.set_tag(tag)


def unset_tag(family: Family, tag: FamilyTag) -> None:
    for person in family.persons.values():
        person.unset_tag(tag)


def set_attr(family: Family, label: str, value: Any) -> None:
    for person in family.persons.values():
        person.set_attr(label, value)


def check_tag(family: Family, tag: FamilyTag) -> bool:
    for person in family.persons.values():
        if not person.has_tag(tag):
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
    if check_nuclear_family(family):
        set_tag(family, FamilyTag.NUCLEAR)
        return True
    unset_tag(family, FamilyTag.NUCLEAR)
    return False


def check_quad_family(family: Family) -> bool:
    if len(family) != 4:
        return False
    if not check_nuclear_family(family):
        return False

    return True


def tag_quad_family(family: Family) -> bool:
    """Set quad family tag to the family."""
    if check_quad_family(family):
        set_tag(family, FamilyTag.QUAD)
        return True
    unset_tag(family, FamilyTag.QUAD)
    return False


def check_trio_family(family: Family) -> bool:
    if len(family) != 3:
        return False
    if not check_nuclear_family(family):
        return False

    return True


def tag_trio_family(family: Family) -> bool:
    """Set trio family tag to the family."""
    if check_trio_family(family):
        set_tag(family, FamilyTag.TRIO)
        return True
    unset_tag(family, FamilyTag.TRIO)
    return False


def check_simplex_family(family: Family) -> bool:
    return len(list(filter(
        lambda p: p.status == Status.affected,
        family.persons.values()))) == 1


def tag_simplex_family(family: Family) -> bool:
    """Set simplex family tag to the family."""
    if check_simplex_family(family):
        set_tag(family, FamilyTag.SIMPLEX)
        return True
    unset_tag(family, FamilyTag.SIMPLEX)
    return False


def check_multiplex_family(family: Family) -> bool:
    return len(list(filter(
        lambda p: p.status == Status.affected,
        family.persons.values()))) > 1


def tag_multiplex_family(family: Family) -> bool:
    """Set multiplex family tag to the family."""
    if check_multiplex_family(family):
        set_tag(family, FamilyTag.MULTIPLEX)
        return True
    unset_tag(family, FamilyTag.MULTIPLEX)
    return False


def check_control_family(family: Family) -> bool:
    return len(list(filter(
        lambda p: p.status == Status.affected,
        family.persons.values()))) == 0


def tag_control_family(family: Family) -> bool:
    """Set control family tag to the family."""
    if check_control_family(family):
        set_tag(family, FamilyTag.CONTROL)
        return True
    unset_tag(family, FamilyTag.CONTROL)
    return False


def check_affected_dad_family(family: Family) -> bool:
    dad = _get_dad(family)
    if dad is None:
        return False
    return bool(dad.status == Status.affected)


def tag_affected_dad_family(family: Family) -> bool:
    """Set affected dad family tag to the family."""
    if check_affected_dad_family(family):
        set_tag(family, FamilyTag.AFFECTED_DAD)
        return True
    unset_tag(family, FamilyTag.AFFECTED_DAD)
    return False


def check_affected_mom_family(family: Family) -> bool:
    mom = _get_mom(family)
    if mom is None:
        return False
    return bool(mom.status == Status.affected)


def tag_affected_mom_family(family: Family) -> bool:
    """Set affected mom family tag to the family."""
    if check_affected_mom_family(family):
        set_tag(family, FamilyTag.AFFECTED_MOM)
        return True
    unset_tag(family, FamilyTag.AFFECTED_MOM)
    return False


def check_affected_prb_family(family: Family) -> bool:
    prb = _get_prb(family)
    if prb is None:
        return False
    return bool(prb.status == Status.affected)


def tag_affected_prb_family(family: Family) -> bool:
    """Set affected proband family tag to the family."""
    if check_affected_prb_family(family):
        set_tag(family, FamilyTag.AFFECTED_PRB)
        return True
    unset_tag(family, FamilyTag.AFFECTED_PRB)
    return False


def check_affected_sib_family(family: Family) -> bool:
    for sib in _get_sibs(family):
        if sib.status == Status.affected:
            return True
    return False


def tag_affected_sib_family(family: Family) -> bool:
    """Set affected sibling family tag to the family."""
    if check_affected_sib_family(family):
        set_tag(family, FamilyTag.AFFECTED_SIB)
        return True
    unset_tag(family, FamilyTag.AFFECTED_SIB)
    return False


def check_unaffected_dad_family(family: Family) -> bool:
    dad = _get_dad(family)
    if dad is None:
        return False
    return bool(dad.status == Status.unaffected)


def tag_unaffected_dad_family(family: Family) -> bool:
    """Set unaffected dad family tag to the family."""
    if check_unaffected_dad_family(family):
        set_tag(family, FamilyTag.UNAFFECTED_DAD)
        return True
    unset_tag(family, FamilyTag.UNAFFECTED_DAD)
    return False


def check_unaffected_mom_family(family: Family) -> bool:
    mom = _get_mom(family)
    if mom is None:
        return False
    return bool(mom.status == Status.unaffected)


def tag_unaffected_mom_family(family: Family) -> bool:
    """Set unaffected mom family tag to the family."""
    if check_unaffected_mom_family(family):
        set_tag(family, FamilyTag.UNAFFECTED_MOM)
        return True
    unset_tag(family, FamilyTag.UNAFFECTED_MOM)
    return False


def check_unaffected_prb_family(family: Family) -> bool:
    prb = _get_prb(family)
    if prb is None:
        return False
    return bool(prb.status == Status.unaffected)


def tag_unaffected_prb_family(family: Family) -> bool:
    """Set unaffected proband family tag to the family."""
    if check_unaffected_prb_family(family):
        set_tag(family, FamilyTag.UNAFFECTED_PRB)
        return True
    unset_tag(family, FamilyTag.UNAFFECTED_PRB)
    return False


def check_unaffected_sib_family(family: Family) -> bool:
    for sib in _get_sibs(family):
        if sib.status == Status.unaffected:
            return True
    return False


def tag_unaffected_sib_family(family: Family) -> bool:
    """Set unaffected sibling family tag to the family."""
    if check_unaffected_sib_family(family):
        set_tag(family, FamilyTag.UNAFFECTED_SIB)
        return True
    unset_tag(family, FamilyTag.UNAFFECTED_SIB)
    return False


def check_male_prb_family(family: Family) -> bool:
    prb = _get_prb(family)
    if prb is None:
        return False
    return bool(prb.sex == Sex.male)


def tag_male_prb_family(family: Family) -> bool:
    """Set male proband family tag to the family."""
    if check_male_prb_family(family):
        set_tag(family, FamilyTag.MALE_PRB)
        return True
    unset_tag(family, FamilyTag.MALE_PRB)
    return False


def check_female_prb_family(family: Family) -> bool:
    prb = _get_prb(family)
    if prb is None:
        return False
    return bool(prb.sex == Sex.female)


def tag_female_prb_family(family: Family) -> bool:
    """Set female proband family tag to the family."""
    if check_female_prb_family(family):
        set_tag(family, FamilyTag.FEMALE_PRB)
        return True
    unset_tag(family, FamilyTag.FEMALE_PRB)
    return False


def check_missing_mom_family(family: Family) -> bool:
    if _get_mom(family) is None:
        return True
    return False


def tag_missing_mom_family(family: Family) -> bool:
    """Set missing mom family tag to the family."""
    if check_missing_mom_family(family):
        set_tag(family, FamilyTag.MISSING_MOM)
        return True
    unset_tag(family, FamilyTag.MISSING_MOM)
    return False


def check_missing_dad_family(family: Family) -> bool:
    if _get_dad(family) is None:
        return True
    return False


def tag_missing_dad_family(family: Family) -> bool:
    """Set missing dad family tag to the family."""
    if check_missing_dad_family(family):
        set_tag(family, FamilyTag.MISSING_DAD)
        return True
    unset_tag(family, FamilyTag.MISSING_DAD)
    return False


def _build_family_type_full(family: Family) -> str:
    family_type = []
    family_type.append(str(len(family.members_in_order)))
    members_by_role_and_sex = sorted(
        family.members_in_order, key=lambda p: f"{p.role}.{p.sex}")
    for person in members_by_role_and_sex:
        family_type.append(
            f"{person.role}.{person.sex}.{person.status}"
        )
    return ":".join(family_type)


class FamilyTagsBuilder:
    """Class used ot apply all tags to a family."""

    TAGS: dict[FamilyTag, Callable[[Family], bool]] = {
        FamilyTag.NUCLEAR: tag_nuclear_family,
        FamilyTag.QUAD: tag_quad_family,
        FamilyTag.TRIO: tag_trio_family,
        FamilyTag.SIMPLEX: tag_simplex_family,
        FamilyTag.MULTIPLEX: tag_multiplex_family,
        FamilyTag.CONTROL: tag_control_family,
        FamilyTag.AFFECTED_DAD: tag_affected_dad_family,
        FamilyTag.AFFECTED_MOM: tag_affected_mom_family,
        FamilyTag.AFFECTED_PRB: tag_affected_prb_family,
        FamilyTag.AFFECTED_SIB: tag_affected_sib_family,
        FamilyTag.UNAFFECTED_DAD: tag_unaffected_dad_family,
        FamilyTag.UNAFFECTED_MOM: tag_unaffected_mom_family,
        FamilyTag.UNAFFECTED_PRB: tag_unaffected_prb_family,
        FamilyTag.UNAFFECTED_SIB: tag_unaffected_sib_family,
        FamilyTag.MALE_PRB: tag_male_prb_family,
        FamilyTag.FEMALE_PRB: tag_female_prb_family,
        FamilyTag.MISSING_MOM: tag_missing_mom_family,
        FamilyTag.MISSING_DAD: tag_missing_dad_family,
    }

    def __init__(self) -> None:
        self._taggers = {}
        self._taggers.update(self.TAGS)
        self._family_types: dict[str, str] = {}

    def add_tagger(
            self, tag: FamilyTag,
            tagger: Callable[[Family], bool]) -> None:
        self._taggers[tag] = tagger

    def tag_family(self, family: Family) -> None:
        """Tag family with all available tags."""
        for tag, tagger in self._taggers.items():
            value = tagger(family)
            if value is None:
                continue
            if isinstance(value, bool):
                if value:
                    family.set_tag(tag)
                continue

    def _tag_family_type(self, family: Family) -> None:
        """Tag a family with family type tags - short and full."""
        full_type = _build_family_type_full(family)
        if full_type not in self._family_types:
            short_type = f"type#{len(self._family_types) + 1}"
            self._family_types[full_type] = short_type
        short_type = self._family_types[full_type]
        set_attr(family, "tag_family_type", short_type)
        set_attr(family, "tag_family_type_full", full_type)

    def tag_families_data(self, families: FamiliesData) -> None:
        self._family_types = self._prebuild_family_types(families)
        for family in families.values():
            self.tag_family(family)
            self._tag_family_type(family)

    @staticmethod
    def _prebuild_family_types(families: FamiliesData) -> dict[str, str]:
        counter: Counter[str] = Counter()
        for family in families.values():
            full_type = _build_family_type_full(family)
            counter[full_type] += 1

        def type_order(full_type: str) -> int:
            return counter[full_type]

        all_types = sorted(
            counter.keys(), key=type_order, reverse=True)
        result: dict[str, str] = {}
        for index, full_type in enumerate(all_types):
            result[full_type] = f"type#{index + 1}"
        return result
