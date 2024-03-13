# pylint: disable=W0621,C0114,C0116,W0212,W0613
from studies.query_transformer import QueryTransformer
from gpf_instance.gpf_instance import WGPFInstance


def test_transform_family_tags_kwargs(
    wdae_gpf_instance: WGPFInstance
) -> None:
    query_transformer = QueryTransformer(
        wdae_gpf_instance.get_wdae_wrapper("Study1")
    )

    # Test simple select tag filer
    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_male_prb_family"
        ]
    )
    assert kwargs["family_ids"] == {"f10", "f6", "f9"}

    # Test simple deselect tag filer
    kwargs = query_transformer.transform_kwargs(
        tagIntersection=False,
        deselectedFamilyTags=[
            "tag_trio_family"
        ]
    )
    assert kwargs["family_ids"] == {"f4", "f9", "f10"}

    # Test or mode between two filters
    kwargs = query_transformer.transform_kwargs(
        tagIntersection=False,
        selectedFamilyTags=[
            "tag_male_prb_family",
            "tag_female_prb_family"
        ]
    )
    assert kwargs["family_ids"] == {
        "f5",
        "f1",
        "f7",
        "f8",
        "f6",
        "f4",
        "f11",
        "f10",
        "f3",
        "f9"
    }

    # Test and mode between two filters
    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_missing_dad_family",
            "tag_missing_mom_family"
        ]
    )
    assert kwargs["family_ids"] == {"f9", "f10"}

    # Test selection with deselection
    kwargs = query_transformer.transform_kwargs(
        selectedFamilyTags=[
            "tag_missing_dad_family",
        ],
        deselectedFamilyTags=[
            "tag_missing_mom_family"
        ]
    )
    assert kwargs["family_ids"] == {"f4"}
