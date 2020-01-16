import pytest

from dae.common_reports.family_counter import FamilyCounter, \
    FamiliesGroupCounters


def test_family_counter(study1, families_groups):
    fgs = families_groups(study1)
    fg = fgs.get('phenotype')
    family = study1.families['f5']

    pedigree = fg.family_pedigree(family)
    family_counter = FamilyCounter(pedigree, 1)

    assert family_counter.pedigree[0] == \
        ['f5', 'mom5', '0', '0', 'F', 'mom', '#e35252', None, False, '', '']
    assert family_counter.pedigree[1] == \
        ['f5', 'dad5', '0', '0', 'M', 'dad', '#aaaaaa', None, False, '', '']
    assert family_counter.pedigree[2] == \
        ['f5', 'ch5', 'mom5', 'dad5', 'F', 'prb', '#e35252', None, False, '',
         '']
    assert family_counter.pedigree[3] == \
        ['f5', 'ch5.1', 'mom5', 'dad5', 'F', 'sib', '#E0E0E0', None, True, '',
         '']
    assert family_counter.pedigrees_label == 1

    assert len(family_counter.to_dict().keys()) == 2


@pytest.mark.xfail
def test_families_group_counter(families_groups, study1):
    fg = families_groups(study1)
    families_group_counter = FamiliesGroupCounters(
        fg,
        fg['phenotype'],
        False, False
    )

    assert len(families_group_counter.counters) == 8
    assert len(families_group_counter.counters[0].pedigree) == 3
    assert len(families_group_counter.counters[1].pedigree) == 3
    assert len(families_group_counter.counters[2].pedigree) == 4

    assert len(families_group_counter.to_dict().keys()) == 4


def test_families_group_counter_draw_all(study1, families_groups):
    fg = families_groups(study1)
    counter = FamiliesGroupCounters(
        fg,
        fg.get_families_group('phenotype'),
        True, False
    )
    assert len(counter.to_dict().keys()) == 4

    assert len(counter.counters) == \
        len(fg.families)


def test_families_group_counter_same(study1, families_groups):
    # families_list = [
    #     study1.families['f1'], study1.families['f3'], study1.families['f6'],
    #     study1.families['f9'], study1.families['f10']
    # ]
    fg = families_groups(study1)

    families_group_counter = FamiliesGroupCounters(
        fg,
        fg.get_families_group('phenotype'),
        False, False
    )

    assert len(families_group_counter.counters) == 8

    assert len(families_group_counter.to_dict().keys()) == 4


def test_families_group_counters(study1, families_groups):
    fg = families_groups(study1)

    families_group_counters = FamiliesGroupCounters(
        fg,
        fg.get_families_group('phenotype'),
        False, False
    )

    assert families_group_counters.selected_families_group.name == 'Diagnosis'
    assert families_group_counters.selected_families_group.available_values \
        == ['phenotype1', 'phenotype2', 'unaffected', 'unknown']

    assert len(families_group_counters.counters) == 8
    assert len(families_group_counters.selected_families_group.legend) == 6

    assert families_group_counters.selected_families_group.legend[-1]['id'] \
        == 'missing-person'

    assert len(families_group_counters.to_dict().keys()) == 4


def test_families_group_counter_study2(study2, families_groups):
    fg = families_groups(study2)
    families_group_counters = FamiliesGroupCounters(
        fg,
        fg.get_families_group('phenotype'),
        False, False
    )
    assert len(families_group_counters.counters) == 4
