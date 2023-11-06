# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
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
        == "enrichment/coding_len_testing"
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
) -> None:
    enrichment_config = f1_trio_enrichment_config
    assert enrichment_config.selected_background_models == [
        "enrichment/coding_len_testing",
        "enrichment/samocha_testing",
    ]


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
