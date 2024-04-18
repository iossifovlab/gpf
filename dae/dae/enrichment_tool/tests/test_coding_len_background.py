# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.enrichment_tool.event_counters import (
    EventCountersResult,
    EventsCounter,
    overlap_event_counts,
)
from dae.enrichment_tool.gene_weights_background import (
    GeneWeightsEnrichmentBackground,
)
from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.studies.study import GenotypeData
from dae.variants.attributes import Inheritance


def test_load(coding_len_background: GeneWeightsEnrichmentBackground) -> None:
    assert coding_len_background.is_loaded()

    assert coding_len_background.genes_weight(["SAMD11"]) == 3.0
    assert coding_len_background.genes_weight(["PLEKHN1"]) == 7.0
    assert coding_len_background.genes_weight(["POGZ"]) == 13.0


def test_calc_stats(
        f1_trio: GenotypeData,
        coding_len_background: GeneWeightsEnrichmentBackground) -> None:
    # pylint: disable=too-many-statements
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name)),
    )

    for fv in variants:
        print(80 * "-")
        print(fv, fv.effects)
        for fa in fv.alleles:
            print("\t", fa, fa.effects)

    event_counter = EventsCounter()

    psc = f1_trio.get_person_set_collection("phenotype")
    assert psc is not None

    # genotype_helper = GenotypeHelper(f1_trio, psc)
    # children_stats = genotype_helper.get_children_stats("phenotype1")
    children_by_sex = psc.person_sets["phenotype1"].get_children_by_sex()
    variant_events = GenotypeHelper.collect_denovo_events(variants)
    enrichment_events = event_counter.events(
        variant_events, children_by_sex, set(["missense", "synonymous"]),
    )

    assert enrichment_events.all is not None
    assert len(enrichment_events.all) == 2
    assert enrichment_events.all == [["SAMD11"], ["SAMD11"]]

    assert enrichment_events.rec is not None
    assert len(enrichment_events.rec) == 1
    assert enrichment_events.rec == [["SAMD11"]]

    assert enrichment_events.male is not None
    assert len(enrichment_events.male) == 1
    assert enrichment_events.male == [["SAMD11"]]

    assert enrichment_events.female is not None
    assert len(enrichment_events.female) == 1
    assert enrichment_events.female == [["SAMD11"]]

    assert enrichment_events.unspecified is not None
    assert len(enrichment_events.unspecified) == 0

    result = coding_len_background.calc_enrichment_test(
        EventCountersResult.from_events_result(enrichment_events),
        overlap_event_counts(enrichment_events, ["SAMD11", "PLEKHN1", "POGZ"]),
        ["SAMD11", "PLEKHN1", "POGZ"],
    )

    assert result.all.events == 2
    assert result.all.expected == 2.0
    assert result.all.pvalue == 1.0

    assert result.rec.events == 1
    assert result.rec.expected == 1.0
    assert result.rec.pvalue == 1.0

    assert result.male.events == 1
    assert result.male.expected == 1.0
    assert result.male.pvalue == 1.0

    assert result.female.events == 1
    assert result.female.expected == 1.0
    assert result.female.pvalue == 1.0

    assert result.unspecified.events == 0
    assert result.unspecified.expected == 0.0
    assert result.unspecified.pvalue == 1.0
