# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.testing import build_inmemory_test_resource, \
    convert_to_tab_separated
from dae.genomic_resources.repository import GR_CONF_FILE_NAME

from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground


def test_background_resource_simple() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: gene_weights_enrichment_background
            filename: data.mem
        """,
        "data.mem": convert_to_tab_separated("""
            gene   gene_weight
            A      10
            B      10
            C      10
            D      20
            E      20
            F      20
        """)
    })
    assert res.get_type() == "gene_weights_enrichment_background"

    background = GeneWeightsEnrichmentBackground(res)
    assert background is not None

    background.load()

    assert background.is_loaded()
    assert background._total == 90
