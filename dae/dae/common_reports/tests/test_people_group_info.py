from dae.pedigrees.families_groups import PeopleGroup, FamiliesGroup


def test_people_group_info(people_groups):
    people_group_info = PeopleGroup.from_config(
        'phenotype', people_groups.phenotype
    )

    assert people_group_info.name == 'Diagnosis'
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
    assert list(people_group_info.domain.keys()) == \
        ['phenotype1', 'phenotype2', 'phenotype3', 'unaffected']
    assert people_group_info.default.id == 'unknown'
    assert people_group_info.default.name == 'unknown'
    assert people_group_info.default.color == '#aaaaaa'
    assert people_group_info.source == 'study.phenotype'


def test_families_group(people_groups, study2):
    people_group = PeopleGroup.from_config(
        'phenotype', people_groups.phenotype
    )
    families_group = FamiliesGroup(study2.families, people_group)

    assert families_group.available_values == \
        ['phenotype1', 'phenotype2', 'unaffected', 'unknown']

    assert people_group.missing_person.id == 'missing-person'
    assert people_group.missing_person.name == 'missing-person'
    assert people_group.missing_person.color == '#E0E0E0'


def test_people_groups_info(study1, families_groups):
    fg = families_groups(study1)
    assert len(fg) == 6

    assert fg.get_default_families_group() == \
        next(iter(fg.values()))
    assert fg.has_families_group('phenotype') is True
    assert fg.has_families_group('pheno') is False
    assert fg.get_families_group('pheno') is None
