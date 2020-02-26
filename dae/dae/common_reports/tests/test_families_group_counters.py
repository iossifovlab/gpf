import pytest
import os
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_groups import (
    FamiliesGroups,
    PeopleMultiGroup,
    PEOPLE_GROUP_ROLES,
    PEOPLE_GROUP_SEXES,
)

from dae.common_reports.family_counter import FamiliesGroupCounters


def relative_to_this_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.mark.parametrize(
    "pedigree,count",
    [
        ("pedigree_A.ped", 1),
        ("pedigree_2.ped", 2),
        ("pedigree_B.ped", 2),
        ("pedigree_C.ped", 1),
        ("pedigree_D.ped", 2),
    ],
)
def test_families_group_counter(pedigree, count):
    pedigree_filename = relative_to_this_folder(f"fixtures/{pedigree}")
    families_loader = FamiliesLoader(pedigree_filename)
    families = families_loader.load()

    assert families is not None

    families_groups = FamiliesGroups(families)
    families_groups.add_predefined_groups(
        ["status", "family_size", "role", "sex", "role.sex",]
    )
    assert len(families_groups) == 5

    selected_families_group = families_groups["status"]
    fgc = FamiliesGroupCounters(
        families_groups, selected_families_group, False, False
    )
    assert fgc is not None

    assert len(fgc.counters) == count


def test_people_multi_group():
    pg = PeopleMultiGroup([PEOPLE_GROUP_ROLES, PEOPLE_GROUP_SEXES])
    assert pg is not None

    from pprint import pprint

    pprint(pg.domain)
    assert pg.id == "role.sex"
    assert pg.name == "Role and Sex"

    assert "('prb', 'M')" in pg.domain
    assert pg.domain["('prb', 'M')"].id == "('prb', 'M')"
    assert pg.domain["('prb', 'M')"].name == ("prb", "M")
    assert pg.domain["('prb', 'M')"].color == "#bfbfbf"

    assert pg.default.id == "('unknown', 'U')"

    assert pg.default.color == "#bbbbbb"


def test_people_multi_group_getter():
    pedigree_filename = relative_to_this_folder(f"fixtures/pedigree_D.ped")
    families_loader = FamiliesLoader(pedigree_filename)
    families = families_loader.load()

    f1_sib = families.persons["f1.s1"]
    f2_sib = families.persons["f2.s1"]

    pg = PeopleMultiGroup([PEOPLE_GROUP_ROLES, PEOPLE_GROUP_SEXES])

    assert pg.getter(f1_sib) == "('sib', 'F')"
    assert pg.getter(f2_sib) == "('sib', 'M')"

    assert pg.domain[pg.getter(f1_sib)].id == "('sib', 'F')"
    assert pg.domain[pg.getter(f2_sib)].id == "('sib', 'M')"


def test_role_sex_available_family_types():
    pedigree_filename = relative_to_this_folder(f"fixtures/pedigree_D.ped")
    families_loader = FamiliesLoader(pedigree_filename)
    families = families_loader.load()

    assert families is not None

    families_groups = FamiliesGroups(families)
    families_groups.add_predefined_groups(
        ["status", "family_size", "role", "sex", "role.sex",]
    )
    assert len(families_groups) == 5

    rs_group = families_groups["role.sex"]
    assert rs_group is not None

    from pprint import pprint

    pprint("families_types:")
    pprint(rs_group.families_types)
    pprint("available_families_types:")
    pprint(rs_group.available_families_types)
