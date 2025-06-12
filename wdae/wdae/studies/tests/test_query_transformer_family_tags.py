# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

from gpf_instance.gpf_instance import WGPFInstance

from dae.studies.study import GenotypeDataStudy
from studies.query_transformer import make_query_transformer
from studies.study_wrapper import WDAEStudy


def test_transform_selected_family_tags_kwargs(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_study_1_wrapper: WDAEStudy,
) -> None:
    query_transformer = make_query_transformer(t4c8_wgpf_instance)
    genotype_data = cast(GenotypeDataStudy, t4c8_study_1_wrapper.genotype_data)

    # Test simple select tag filer
    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        selectedFamilyTags=[
            "tag_male_prb_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(kwargs["tags_query"])
    assert family_ids == set()

    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        selectedFamilyTags=[
            "tag_female_prb_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(kwargs["tags_query"])
    assert family_ids == {"f1.1", "f1.3"}


def test_transform_deselected_family_tags_kwargs(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_study_1_wrapper: WDAEStudy,
) -> None:
    query_transformer = make_query_transformer(t4c8_wgpf_instance)
    genotype_data = cast(GenotypeDataStudy, t4c8_study_1_wrapper.genotype_data)

    # Test simple deselect tag filer
    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        tagIntersection=False,
        deselectedFamilyTags=[
            "tag_trio_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(kwargs["tags_query"])
    assert family_ids == {"f1.1", "f1.3"}

    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        tagIntersection=False,
        deselectedFamilyTags=[
            "tag_male_prb_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(kwargs["tags_query"])
    assert family_ids == {"f1.1", "f1.3"}

    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        tagIntersection=False,
        deselectedFamilyTags=[
            "tag_affected_sib_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(
        kwargs["tags_query"],
    )
    assert family_ids == {"f1.1", "f1.3"}


def test_transform_or_mode_family_tags_kwargs(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_study_1_wrapper: WDAEStudy,
) -> None:
    query_transformer = make_query_transformer(t4c8_wgpf_instance)
    genotype_data = cast(GenotypeDataStudy, t4c8_study_1_wrapper.genotype_data)

    # Test or mode between two filters
    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        tagIntersection=False,
        selectedFamilyTags=[
            "tag_male_prb_family",
            "tag_female_prb_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(
        kwargs["tags_query"],
    )
    assert family_ids == {"f1.1", "f1.3"}


def test_transform_and_mode_family_tags_kwargs(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_study_1_wrapper: WDAEStudy,
) -> None:
    query_transformer = make_query_transformer(t4c8_wgpf_instance)
    genotype_data = cast(GenotypeDataStudy, t4c8_study_1_wrapper.genotype_data)

    # Test and mode between two filters
    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        selectedFamilyTags=[
            "tag_missing_dad_family",
            "tag_missing_mom_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(
        kwargs["tags_query"],
    )
    assert family_ids == set()

    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        selectedFamilyTags=[
            "tag_affected_prb_family",
            "tag_unaffected_sib_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(
        kwargs["tags_query"],
    )
    assert family_ids == {"f1.1", "f1.3"}


def test_transform_complex_family_tags_kwargs(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_study_1_wrapper: WDAEStudy,
) -> None:
    query_transformer = make_query_transformer(t4c8_wgpf_instance)
    genotype_data = cast(GenotypeDataStudy, t4c8_study_1_wrapper.genotype_data)

    # Test selection with deselection
    kwargs = query_transformer.transform_kwargs(
        t4c8_study_1_wrapper,
        selectedFamilyTags=[
            "tag_female_prb_family",
        ],
        deselectedFamilyTags=[
            "tag_missing_mom_family",
        ],
    )
    family_ids = genotype_data.backend.tags_to_family_ids(
        kwargs["tags_query"],
    )
    assert family_ids == {"f1.1", "f1.3"}
