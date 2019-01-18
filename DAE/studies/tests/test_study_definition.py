def test_fixture_study_definition_is_loaded(study_definitions):
    expected = {
        'inheritance_trio', 'quads_two_families',
        'quads_variant_types', 'quads_in_parent',
        'quads_f1', 'quads_in_child'
    }

    assert study_definitions is not None
    studies = list(study_name for study_name in study_definitions.configs)

    assert set(studies) == expected
