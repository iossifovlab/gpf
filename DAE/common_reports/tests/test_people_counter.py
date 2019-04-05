def test_people_counter(pc_s1_mom_and_phenotype1):
    assert pc_s1_mom_and_phenotype1.people_male == 0
    assert pc_s1_mom_and_phenotype1.people_female == 2
    assert pc_s1_mom_and_phenotype1.people_unspecified == 0
    assert pc_s1_mom_and_phenotype1.people_total == 2

    assert pc_s1_mom_and_phenotype1.column == 'mom and phenotype1'

    assert pc_s1_mom_and_phenotype1.is_empty() is False
    assert pc_s1_mom_and_phenotype1.is_empty_field('people_male') is True
    assert pc_s1_mom_and_phenotype1.is_empty_field('people_female') is False

    assert len(pc_s1_mom_and_phenotype1.to_dict(
        ['people_female', 'people_total']).keys()) == 3


def test_people_counter_empty(pc_s1_dad_and_phenotype1):
    assert pc_s1_dad_and_phenotype1.people_male == 0
    assert pc_s1_dad_and_phenotype1.people_female == 0
    assert pc_s1_dad_and_phenotype1.people_unspecified == 0
    assert pc_s1_dad_and_phenotype1.people_total == 0

    assert pc_s1_dad_and_phenotype1.column == 'dad and phenotype1'

    assert pc_s1_dad_and_phenotype1.is_empty() is True
    assert pc_s1_dad_and_phenotype1.is_empty_field('people_male') is True

    assert len(pc_s1_dad_and_phenotype1.to_dict([]).keys()) == 1


def test_people_counters(people_counters):
    assert len(people_counters.counters) == 6
    assert people_counters.group_name == 'Role and Diagnosis'
    assert people_counters.rows == \
        ['people_male', 'people_female', 'people_total']
    assert sorted(people_counters.columns) == sorted(
        ['sib and phenotype2', 'prb and phenotype1', 'mom and unaffected',
         'mom and phenotype1', 'dad and pheno', 'dad and unaffected'])

    assert len(people_counters.to_dict().keys()) == 4
