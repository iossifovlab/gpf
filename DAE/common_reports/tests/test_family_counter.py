def test_family_counter(family_counter):
    assert family_counter.pedigree[0] == \
        ['f5', 'mom5', '', '', 'F', 'mom', '#e35252', None, False, '', '']
    assert family_counter.pedigree[1] == \
        ['f5', 'dad5', '', '', 'M', 'dad', '#aaaaaa', None, False, '', '']
    assert family_counter.pedigree[2] == \
        ['f5', 'ch5', 'dad5', 'mom5', 'F', 'prb', '#e35252', None, False, '',
         '']
    assert family_counter.pedigree[3] == \
        ['f5', 'ch5.1', 'dad5', 'mom5', 'F', 'sib', '#E0E0E0', None, True, '',
         '']
    assert family_counter.pedigrees_count == 1

    assert len(family_counter.to_dict().keys()) == 2


def test_families_counter(families_counter):
    assert len(families_counter.counters) == 3
    assert len(families_counter.counters[0].pedigree) == 4
    assert len(families_counter.counters[1].pedigree) == 4
    assert len(families_counter.counters[2].pedigree) == 3

    assert len(families_counter.to_dict().keys()) == 1


def test_families_counter_draw_all(families_counter_draw_all):
    assert len(families_counter_draw_all.counters) == 4

    assert len(families_counter_draw_all.to_dict().keys()) == 1


def test_families_counter_same(families_counter_same):
    assert len(families_counter_same.counters) == 4

    assert len(families_counter_same.to_dict().keys()) == 1


def test_families_counters(families_counters):
    assert families_counters.group_name == 'Study phenotype'
    assert sorted(families_counters.people_groups) == \
        sorted(['phenotype1', 'phenotype2', 'pheno', 'unaffected'])
    assert len(families_counters.counters) == 3
    assert len(families_counters.legend) == 6
    assert families_counters.legend[-1]['id'] == 'missing-person'

    assert len(families_counters.to_dict().keys()) == 4
