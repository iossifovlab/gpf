# pylint: disable=W0621,C0114,C0116,W0212,W0613

from box import Box


def test_fixture_study_config_parser_is_loaded(
    genotype_data_study_configs: dict[str, Box],
) -> None:
    expected = {
        "f1_study",
        "f1_trio",
        "f2_recurrent",
        "f3_triple",
        "fake_study",
        "inheritance_trio",
        "quads_f1",  # 'quads_f1_impala',
        "quads_f2",
        "quads_in_child",
        "quads_in_parent",
        "quads_two_families",
        "quads_variant_types",
        "Study1",
        "Study2",
        "Study3",
        "study4",
        "person_sets_study_1",
        "person_sets_study_2",
        "person_sets_study_3",
        "comp",
    }

    assert genotype_data_study_configs is not None
    studies = list(study_name for study_name in genotype_data_study_configs)

    assert set(studies) == expected
