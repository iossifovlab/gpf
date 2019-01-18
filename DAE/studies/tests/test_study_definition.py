def test_fixture_study_definition_is_loaded(study_definition):
    expected = {
        'inheritance_trio', 'quads_two_families',
        'quads_variant_types', 'quads_in_parent',
        'quads_f1', 'quads_in_child'
    }

    assert study_definition is not None
    studies = list(study_name for study_name in study_definition.configs)

    assert set(studies) == expected
