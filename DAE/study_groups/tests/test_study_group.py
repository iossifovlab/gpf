def test_can_get_study_group_from_config(basic_groups_definition):
    configs = basic_groups_definition.get_all_study_group_configs()

    assert configs is not None
    assert len(configs) != 0


def test_skips_unknown_study_names(basic_groups_definition):
    configs = basic_groups_definition.get_all_study_group_configs()

    assert configs is not None
    assert len(configs) == 1
    assert configs[0].name == 'test'
