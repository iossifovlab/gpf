def test_study_group_facade_is_loaded(study_group_facade):
    assert study_group_facade is not None


def test_study_group_facade_has_all_study_groups(study_group_facade):
    assert study_group_facade.get_all_study_group_ids() == [
        'test', 'phenotypes'
    ]
