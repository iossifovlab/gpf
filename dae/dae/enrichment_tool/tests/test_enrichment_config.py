# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
from typing import Callable
from box import Box


def test_enrichment_config_people_groups(
        f1_trio_enrichment_config: Box) -> None:
    enrichment_config = f1_trio_enrichment_config
    assert enrichment_config.selected_person_set_collections == ["phenotype"]


def test_enrichment_config_default_values(
        f1_trio_enrichment_config: Box) -> None:
    enrichment_config = f1_trio_enrichment_config
    assert (
        enrichment_config.default_background_model
        == "coding_len_background_model"
    )
    assert (
        enrichment_config.default_counting_model == "enrichment_gene_counting"
    )


def test_enrichment_config_effect_types(
        f1_trio_enrichment_config: Box) -> None:
    enrichment_config = f1_trio_enrichment_config
    assert enrichment_config.effect_types == ["LGDs", "missense", "synonymous"]


def test_enrichment_config_backgrounds(
    f1_trio_enrichment_config: Box,
    fixture_dirname: Callable[[str], str]
) -> None:
    enrichment_config = f1_trio_enrichment_config
    assert enrichment_config.selected_background_values == [
        "coding_len_background_model",
        "samocha_background_model",
    ]

    assert len(enrichment_config.background) == 2
    for _, background in enrichment_config.background.items():
        assert background.kind in set(
            ["coding_len_background_model", "samocha_background_model"]
        )
    # synonymous_background_model = (
    #     enrichment_config.background.synonymous_background_model
    # )
    # assert synonymous_background_model.name == "synonymous_background_model"
    # assert synonymous_background_model.file is None
    # assert synonymous_background_model.desc == "Synonymous Background Model"

    # fmt: off
    coding_len_background_model = \
        enrichment_config.background.coding_len_background_model
    # fmt: on
    assert coding_len_background_model.name == "coding_len_background_model"
    assert coding_len_background_model.kind == "coding_len_background_model"
    assert coding_len_background_model.file == fixture_dirname(
        "studies/f1_trio/enrichment/codingLenBackgroundModel.csv"
    )
    assert coding_len_background_model.desc == "Coding Len Background Model"

    samocha_background_model = (
        enrichment_config.background.samocha_background_model
    )
    assert samocha_background_model.name == "samocha_background_model"
    assert samocha_background_model.kind == "samocha_background_model"
    assert samocha_background_model.file == fixture_dirname(
        "studies/f1_trio/enrichment/samochaBackgroundModel.csv"
    )
    assert samocha_background_model.desc == "Samocha Background Model"


def test_enrichment_config_counting(
        f1_trio_enrichment_config: Box) -> None:
    enrichment_config = f1_trio_enrichment_config
    assert enrichment_config.selected_counting_values == [
        "enrichment_events_counting",
        "enrichment_gene_counting",
    ]

    assert len(enrichment_config.counting) == 2
    assert (
        len(
            list(
                filter(
                    lambda x: x.name
                    in enrichment_config.selected_counting_values,
                    enrichment_config.counting.values(),
                )
            )
        )
        == 2
    )

    enrichment_events_counting = (
        enrichment_config.counting.enrichment_events_counting
    )
    assert enrichment_events_counting.name == "enrichment_events_counting"
    assert enrichment_events_counting.file is None
    assert enrichment_events_counting.desc == "Enrichment Events Counting"

    enrichment_gene_counting = (
        enrichment_config.counting.enrichment_gene_counting
    )
    assert enrichment_gene_counting.name == "enrichment_gene_counting"
    assert enrichment_gene_counting.file is None
    assert enrichment_gene_counting.desc == "Enrichment Gene Counting"
