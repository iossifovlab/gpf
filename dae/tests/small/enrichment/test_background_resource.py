# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.enrichment_tool.gene_weights_background import (
    GeneScoreEnrichmentBackground,
    GeneWeightsEnrichmentBackground,
)
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)


def test_background_resource_simple() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: gene_weights_enrichment_background
            filename: data.mem
            name: TestingGeneWeightsBackground
        """,
        "data.mem": convert_to_tab_separated("""
            gene   gene_weight
            A      10
            B      10
            C      10
            D      20
            E      20
            F      20
        """),
    })
    assert res.get_type() == "gene_weights_enrichment_background"

    background = GeneWeightsEnrichmentBackground(res)
    assert background is not None
    assert background.name == "TestingGeneWeightsBackground"

    background.load()

    assert background.is_loaded()
    assert background._total == 90


def test_background_gene_score_resource_simple() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: gene_score
            filename: data.mem
            separator: "\t"
            scores:
            - id: gene_coding_length
              name: coding length background
              desc: Gene coding length enrichment background model
              histogram:
                type: number
                number_of_bins: 10
                x_log_scale: false
                y_log_scale: false
                view_range:
                    min: 0
                    max: 100
        """,
        "data.mem": convert_to_tab_separated("""
            gene   gene_coding_length
            A      10
            B      10
            C      10
            D      20
            E      20
            F      20
        """),
    })
    assert res.get_type() == "gene_score"

    background = GeneScoreEnrichmentBackground(res)
    assert background is not None

    assert background.name == "coding length background"
    assert not background.is_loaded()
    background.load()

    assert background.is_loaded()
    assert background._total == 90
