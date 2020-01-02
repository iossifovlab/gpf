from dae.common_reports.family_counter import FamilyCounter, \
    FamiliesGroupCounter, FamiliesGroupCounters


def test_family_counter(study1, families_groups):
    family_counter = FamilyCounter(
        study1.families['f5'], 1,
        families_groups['phenotype']
    )

    assert family_counter.pedigree[0] == \
        ['f5', 'mom5', None, None, 'F', 'mom', '#e35252', None, False, '', '']
    assert family_counter.pedigree[1] == \
        ['f5', 'dad5', None, None, 'M', 'dad', '#aaaaaa', None, False, '', '']
    assert family_counter.pedigree[2] == \
        ['f5', 'ch5', 'dad5', 'mom5', 'F', 'prb', '#e35252', None, False, '',
         '']
    assert family_counter.pedigree[3] == \
        ['f5', 'ch5.1', 'dad5', 'mom5', 'F', 'sib', '#E0E0E0', None, True, '',
         '']
    assert family_counter.pedigrees_count == 1

    assert len(family_counter.to_dict().keys()) == 2


def test_families_group_counter(families_list, families_groups):
    families_group_counter = FamiliesGroupCounter(
        families_list,
        families_groups['phenotype'],
        False, False
    )

    assert len(families_group_counter.counters) == 3
    assert len(families_group_counter.counters[0].pedigree) == 4
    assert len(families_group_counter.counters[1].pedigree) == 4
    assert len(families_group_counter.counters[2].pedigree) == 3

    assert len(families_group_counter.to_dict().keys()) == 1


def test_families_group_counter_draw_all(families_list, families_groups):
    families_group_counter = FamiliesGroupCounter(
        families_list,
        families_groups.get_families_group('phenotype'),
        True, False
    )

    assert len(families_group_counter.counters) == 4

    assert len(families_group_counter.to_dict().keys()) == 1


def test_families_group_counter_same(study1, families_groups):
    families_list = [
        study1.families['f1'], study1.families['f3'], study1.families['f6'],
        study1.families['f9'], study1.families['f10']
    ]

    families_group_counter = FamiliesGroupCounter(
        families_list,
        families_groups.get_families_group('phenotype'),
        False, False
    )

    assert len(families_group_counter.counters) == 4

    assert len(families_group_counter.to_dict().keys()) == 1


def test_families_group_counters(study1, families_groups):
    families_group_counters = FamiliesGroupCounters(
        study1.families,
        families_groups.get_families_group('phenotype'),
        False, False
    )

    assert families_group_counters.group_name == 'Diagnosis'
    assert sorted(families_group_counters.available_values) == \
        sorted(['phenotype1', 'phenotype2', 'unknown', 'unaffected'])
    assert len(families_group_counters.counters) == 5
    assert len(families_group_counters.legend) == 6
    assert families_group_counters.legend[-1].id == 'missing-person'

    assert len(families_group_counters.to_dict().keys()) == 4
