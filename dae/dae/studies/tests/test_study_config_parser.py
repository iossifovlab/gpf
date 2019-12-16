def test_fixture_study_config_parser_is_loaded(genotype_data_study_configs):
    expected = {
        'inheritance_trio', 'quads_two_families',
        'quads_variant_types', 'quads_in_parent',
        'quads_f1', 'quads_in_child', 'quads_f2'
    }

    assert genotype_data_study_configs is not None
    studies = list(study_name for study_name in genotype_data_study_configs)

    assert set(studies) == expected
