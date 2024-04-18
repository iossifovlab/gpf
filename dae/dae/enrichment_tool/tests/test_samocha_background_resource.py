# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.enrichment_tool.samocha_background import SamochaEnrichmentBackground
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import (
    build_inmemory_test_resource,
    convert_to_tab_separated,
)


def test_background_resource_simple() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: samocha_enrichment_background
            filename: data.mem
        """,
        "data.mem": convert_to_tab_separated("""
"transcript","gene","bp","all","synonymous","missense","nonsense","splice-site","frame-shift","F","M","P_LGDS","P_MISSENSE","P_SYNONYMOUS"
"NM_017582","SAMD11",3,-1,-5,-4,-6,-6,-6,2,2,1.1,1.4,5.7
"NM_017582","PLEKHN1",7,-2,-5,-4,-6,-6,-6,2,2,1.2,1.5,5.8
"NM_014372","POGZ",11,-3,-5,-5,-6,-7,-6,2,2,6.3,4.6,2.9
        """),
    })
    assert res.get_type() == "samocha_enrichment_background"

    background = SamochaEnrichmentBackground(res)
    assert background is not None
    assert background.name == "Samocha's enrichment background model"
    assert background.background_type == "samocha_enrichment_background"

    background.load()

    assert background.is_loaded()
