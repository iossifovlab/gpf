# pylint: disable=W0621,C0114,C0116,W0212,W0613
from studies.query_transformer import QueryTransformer
from studies.study_wrapper import StudyWrapper


def test_transform_selected_family_tags_kwargs(
    t4c8_study_2_wrapper: StudyWrapper,
) -> None:
    query_transformer = QueryTransformer(
        t4c8_study_2_wrapper,
    )

    # Test simple select tag filer
    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_male_prb_family",
        ],
    )
    assert kwargs["family_ids"] == set()

    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_female_prb_family",
        ],
    )
    assert kwargs["family_ids"] == {"f1.1", "f1.3"}


def test_transform_deselected_family_tags_kwargs(
    t4c8_study_2_wrapper: StudyWrapper,
) -> None:
    query_transformer = QueryTransformer(
        t4c8_study_2_wrapper,
    )
    # Test simple deselect tag filer
    kwargs = query_transformer.transform_kwargs(
        tagIntersection=False,
        deselectedFamilyTags=[
            "tag_trio_family",
        ],
    )
    assert kwargs["family_ids"] == {"f1.1", "f1.3"}

    kwargs = query_transformer.transform_kwargs(
        tagIntersection=False,
        deselectedFamilyTags=[
            "tag_male_prb_family",
        ],
    )
    assert kwargs["family_ids"] == {"f1.1", "f1.3"}

    kwargs = query_transformer.transform_kwargs(
        tagIntersection=False,
        deselectedFamilyTags=[
            "tag_affected_sib_family",
        ],
    )
    assert kwargs["family_ids"] == {"f1.1", "f1.3"}


def test_transform_or_mode_family_tags_kwargs(
    t4c8_study_2_wrapper: StudyWrapper,
) -> None:
    query_transformer = QueryTransformer(
        t4c8_study_2_wrapper,
    )
    # Test or mode between two filters
    kwargs = query_transformer.transform_kwargs(
        tagIntersection=False,
        selectedFamilyTags=[
            "tag_male_prb_family",
            "tag_female_prb_family",
        ],
    )
    assert kwargs["family_ids"] == {
        "f1.1",
        "f1.3",
    }


def test_transform_and_mode_family_tags_kwargs(
    t4c8_study_2_wrapper: StudyWrapper,
) -> None:
    query_transformer = QueryTransformer(
        t4c8_study_2_wrapper,
    )
    # Test and mode between two filters
    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_missing_dad_family",
            "tag_missing_mom_family",
        ],
    )
    assert kwargs["family_ids"] == set()

    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_affected_prb_family",
            "tag_unaffected_sib_family",
        ],
    )
    assert kwargs["family_ids"] == {"f1.1", "f1.3"}


def test_transform_complex_family_tags_kwargs(
    t4c8_study_2_wrapper: StudyWrapper,
) -> None:
    query_transformer = QueryTransformer(
        t4c8_study_2_wrapper,
    )
    # Test selection with deselection
    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_female_prb_family",
        ],
        deselectedFamilyTags=[
            "tag_missing_mom_family",
        ],
    )
    assert kwargs["family_ids"] == {"f1.1", "f1.3"}
