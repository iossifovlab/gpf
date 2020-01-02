from dae.common_reports.people_counter import PeopleCounter, PeopleCounters


def test_people_counter(study1, filter_objects):
    filter_object = filter_objects[0].get_filter_object_by_column_name(
        'mom and phenotype1')
    assert filter_object

    people_counter = PeopleCounter(study1.families, filter_object)

    assert people_counter.people_male == 0
    assert people_counter.people_female == 4
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 4

    assert people_counter.column == 'mom and phenotype1'

    assert people_counter.is_empty() is False
    assert people_counter.is_empty_field('people_male') is True
    assert people_counter.is_empty_field('people_female') is False

    assert len(people_counter.to_dict(
        ['people_female', 'people_total']).keys()) == 3


def test_people_counter_empty(study1, filter_objects):
    filter_object = filter_objects[0].get_filter_object_by_column_name(
        'dad and phenotype1')
    assert filter_object

    people_counter = PeopleCounter(study1.families, filter_object)

    assert people_counter.people_male == 0
    assert people_counter.people_female == 0
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 0

    assert people_counter.column == 'dad and phenotype1'

    assert people_counter.is_empty() is True
    assert people_counter.is_empty_field('people_male') is True

    assert len(people_counter.to_dict([]).keys()) == 1


def test_people_counters(study1, filter_objects):
    people_counters = PeopleCounters(study1.families, filter_objects[0])

    assert len(people_counters.counters) == 8
    assert people_counters.group_name == 'Role and Diagnosis'
    assert people_counters.rows == \
        ['people_male', 'people_female', 'people_total']
    assert sorted(people_counters.columns) == sorted(
        ['sib and phenotype1', 'sib and phenotype2', 'prb and phenotype1',
         'prb and phenotype2', 'prb and unaffected', 'mom and unaffected',
         'mom and phenotype1',
         # 'dad and unknown',
         'dad and unaffected'])

    assert len(people_counters.to_dict().keys()) == 4
