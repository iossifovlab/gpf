def test_fixture_study_config_parser_is_loaded(study_configs):
    expected = {
        'inheritance_trio', 'quads_two_families',
        'quads_variant_types', 'quads_in_parent',
        'quads_f1', 'quads_in_child', 'quads_f2'
    }

    assert study_configs is not None
    studies = list(study_name for study_name in study_configs)

    assert set(studies) == expected
