from common_reports.people_group_info import PeopleGroupInfo


def test_people_group_info(people_groups, study2):
    people_group_info = PeopleGroupInfo(
        people_groups['phenotype'], 'phenotype', study=study2
    )

    assert people_group_info.name == 'Study phenotype'
    assert people_group_info.domain['phenotype1'].id == 'phenotype1'
    assert people_group_info.domain['phenotype1'].name == 'phenotype 1'
    assert people_group_info.domain['phenotype1'].color == '#e35252'
    assert people_group_info.domain['phenotype2'].id == 'phenotype2'
    assert people_group_info.domain['phenotype2'].name == 'phenotype 2'
    assert people_group_info.domain['phenotype2'].color == '#b8008a'
    assert people_group_info.domain['phenotype3'].id == 'phenotype3'
    assert people_group_info.domain['phenotype3'].name == 'phenotype 3'
    assert people_group_info.domain['phenotype3'].color == '#e3d252'
    assert people_group_info.domain['unaffected'].id == 'unaffected'
    assert people_group_info.domain['unaffected'].name == 'unaffected'
    assert people_group_info.domain['unaffected'].color == '#ffffff'
    assert people_group_info.default.id == 'unknown'
    assert people_group_info.default.name == 'unknown'
    assert people_group_info.default.color == '#aaaaaa'
    assert people_group_info.source == 'study.phenotype'

    assert sorted(people_group_info.people_groups) == \
        sorted(['unaffected', 'phenotype1', 'phenotype2', 'pheno', 'nan'])
    assert sorted(people_group_info.get_people_groups()) == \
        sorted(['unaffected', 'phenotype1', 'phenotype2', 'unknown'])
    assert people_group_info.people_group == 'phenotype'

    assert people_group_info.missing_person_info['id'] == 'missing-person'
    assert people_group_info.missing_person_info['name'] == 'missing-person'
    assert people_group_info.missing_person_info['color'] == '#E0E0E0'


def test_people_groups_info(people_groups_info):
    assert len(people_groups_info.people_groups_info) == 1

    assert people_groups_info.get_first_people_group_info() == \
        people_groups_info.people_groups_info[0]
    assert people_groups_info.has_people_group_info('phenotype') is True
    assert people_groups_info.has_people_group_info('pheno') is False
    assert people_groups_info.get_people_group_info('phenotype') == \
        people_groups_info.people_groups_info[0]
    assert people_groups_info.get_people_group_info('pheno') == []
