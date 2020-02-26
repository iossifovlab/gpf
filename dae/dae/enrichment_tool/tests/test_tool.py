from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.event_counters import EventsCounter
from dae.enrichment_tool.genotype_helper import GenotypeHelper

from dae.variants.attributes import Inheritance


def test_enrichment_tool(
    f1_trio, f1_trio_enrichment_config, f1_trio_coding_len_background
):
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name))
    )
    event_counter = EventsCounter()
    enrichment_tool = EnrichmentTool(
        f1_trio_enrichment_config, f1_trio_coding_len_background, event_counter
    )
    pg = f1_trio.get_families_group("phenotype")
    gh = GenotypeHelper(f1_trio, pg, "phenotype1")
    # children_stats = gh.get_children_stats()
    children_by_sex = gh.children_by_sex()

    enrichment_events = enrichment_tool.calc(
        ["missense", "synonymous"],
        ["SAMD11", "PLEKHN1", "POGZ"],
        variants,
        children_by_sex,
    )

    assert len(enrichment_events["all"].events) == 2
    assert enrichment_events["all"].events == [["SAMD11"], ["SAMD11"]]
    assert enrichment_events["all"].expected == 2.0
    assert enrichment_events["all"].pvalue == 1.0
    assert len(enrichment_events["rec"].events) == 1
    assert enrichment_events["rec"].events == [["SAMD11"]]
    assert enrichment_events["rec"].expected == 1.0
    assert enrichment_events["rec"].pvalue == 1.0
    assert len(enrichment_events["male"].events) == 1
    assert enrichment_events["male"].events == [["SAMD11"]]
    assert enrichment_events["male"].expected == 1.0
    assert enrichment_events["male"].pvalue == 1.0
    assert len(enrichment_events["female"].events) == 1
    assert enrichment_events["female"].events == [["SAMD11"]]
    assert enrichment_events["female"].expected == 1.0
    assert enrichment_events["female"].pvalue == 1.0
    assert len(enrichment_events["unspecified"].events) == 0
    assert enrichment_events["unspecified"].events == []
    assert enrichment_events["unspecified"].expected is None
    assert enrichment_events["unspecified"].pvalue is None
