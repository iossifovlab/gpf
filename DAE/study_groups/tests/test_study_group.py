def test_can_get_study_group_from_config(basic_study_groups_definition):
    configs = basic_study_groups_definition.get_all_study_group_configs()

    assert configs is not None
    assert len(configs) != 0


def test_skips_unknown_study_names(basic_study_groups_definition):
    configs = basic_study_groups_definition.get_all_study_group_configs()

    assert configs is not None
    assert len(configs) == 2
    assert configs[0].name == 'test'


def test_phenotypes_is_loaded_from_studies(
        basic_study_groups_definition, study_groups_factory):
    study_group_config = basic_study_groups_definition \
        .get_study_group_config('phenotypes')

    print(study_group_config)

    study_group = study_groups_factory.get_study_group(study_group_config)
    assert study_group.phenotypes == {'autism', 'epilepsy'}
