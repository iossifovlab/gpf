# pylint: disable=W0621,C0114,C0116,W0212,W0613
from box import Box

from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground

from dae.variants.attributes import Inheritance
from dae.studies.study import GenotypeData


def test_enrichment_tool(
    f1_trio: GenotypeData,
    f1_trio_enrichment_config: Box,
    coding_len_background: GeneWeightsEnrichmentBackground
) -> None:
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name))
    )
    event_counter = EventsCounter()
    enrichment_tool = EnrichmentTool(
        f1_trio_enrichment_config, coding_len_background, event_counter
    )
    psc = f1_trio.get_person_set_collection("phenotype")
    assert psc is not None

    helper = GenotypeHelper(f1_trio, psc)
    children_by_sex = helper.children_by_sex("phenotype1")
    variant_events = GenotypeHelper.collect_denovo_events(variants)
    enrichment_events = enrichment_tool.calc(
        ["SAMD11", "PLEKHN1", "POGZ"],
        variant_events,
        effect_types=["missense", "synonymous"],
        children_by_sex=children_by_sex,
    )

    assert enrichment_events["all"].events is not None
    assert len(enrichment_events["all"].events) == 2
    assert enrichment_events["all"].events == [["SAMD11"], ["SAMD11"]]
    assert enrichment_events["all"].expected == 2.0
    assert enrichment_events["all"].pvalue == 1.0

    assert enrichment_events["rec"].events is not None
    assert len(enrichment_events["rec"].events) == 1
    assert enrichment_events["rec"].events == [["SAMD11"]]
    assert enrichment_events["rec"].expected == 1.0
    assert enrichment_events["rec"].pvalue == 1.0

    assert enrichment_events["male"].events is not None
    assert len(enrichment_events["male"].events) == 1
    assert enrichment_events["male"].events == [["SAMD11"]]
    assert enrichment_events["male"].expected == 1.0
    assert enrichment_events["male"].pvalue == 1.0

    assert enrichment_events["female"].events is not None
    assert len(enrichment_events["female"].events) == 1
    assert enrichment_events["female"].events == [["SAMD11"]]
    assert enrichment_events["female"].expected == 1.0
    assert enrichment_events["female"].pvalue == 1.0

    assert enrichment_events["unspecified"].events is not None
    assert len(enrichment_events["unspecified"].events) == 0
    assert enrichment_events["unspecified"].events == []
    assert enrichment_events["unspecified"].expected == 0
    assert enrichment_events["unspecified"].pvalue == 1.0
