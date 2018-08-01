from study_groups.study_group import StudyGroup


def test_can_get_study_group_from_config(study_factory):
    test_group = StudyGroup.from_config_file(
        study_factory, './fixtures/study_groups.conf', 'test')

    assert test_group is not None


def test_skips_unknown_study_names(study_factory):
    test_group = StudyGroup.from_config_file(
        study_factory, './fixtures/unknown_study.conf', 'test')

    assert test_group is not None
    assert len(test_group.studies) == 1
