from dae.studies.people_group_config_parser import PeopleGroupConfigParser


def test_people_group_parse_variables():
    assert PeopleGroupConfigParser.SECTION == 'peopleGroup'
    assert PeopleGroupConfigParser.SPLIT_STR_LISTS == \
        ['selectedPeopleGroupValues']
    assert PeopleGroupConfigParser.FILTER_SELECTORS == \
        {'peopleGroup': 'selectedPeopleGroupValues'}


def test_get_config_description(quads_f1_config):
    description = PeopleGroupConfigParser.get_config_description(
        quads_f1_config.people_group_config
    )

    assert list(description.keys()) == ['peopleGroup']

    assert len(description['peopleGroup']) == 1

    assert isinstance(description['peopleGroup'][0]['domain'], list)
