# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.enrichment_tool.event_counters import (
    EVENT_COUNTERS,
    EnrichmentSingleResult,
    EventsCounter,
    GeneEventsCounter,
    filter_denovo_one_event_per_family,
    filter_denovo_one_gene_per_events,
    filter_denovo_one_gene_per_recurrent_events,
    filter_overlapping_events,
    get_sym_2_fn,
)
from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.studies.study import GenotypeData
from dae.variants.attributes import Inheritance


def test_filter_denovo_one_event_per_family(
        f1_trio: GenotypeData) -> None:
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name)),
    )
    assert len(variants) == 5
    variant_events = GenotypeHelper.collect_denovo_events(variants)

    fv = filter_denovo_one_event_per_family(
        variant_events, set(["missense", "synonymous"]),
    )

    assert len(fv) == 3
    assert fv == [["SAMD11"], ["SAMD11"], ["PLEKHN1"]]


def test_filter_denovo_one_gene_per_recurrent_events(
        f1_trio: GenotypeData) -> None:
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name)),
    )
    assert len(variants) == 5
    variant_events = GenotypeHelper.collect_denovo_events(variants)

    fv = filter_denovo_one_gene_per_recurrent_events(
        variant_events, set(["missense", "synonymous"]),
    )

    assert len(fv) == 1
    assert fv == [["SAMD11"]]


def test_filter_denovo_one_gene_per_events(f1_trio: GenotypeData) -> None:
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name)),
    )
    assert len(variants) == 5
    variant_events = GenotypeHelper.collect_denovo_events(variants)

    fv = filter_denovo_one_gene_per_events(
        variant_events, set(["missense", "synonymous"]),
    )

    assert len(fv) == 2
    assert fv == [["PLEKHN1"], ["SAMD11"]]


def test_get_sym_2_fn(f1_trio: GenotypeData) -> None:
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name)),
    )
    assert len(variants) == 5
    variant_events = GenotypeHelper.collect_denovo_events(variants)

    sym_2_fn = get_sym_2_fn(variant_events, set(["missense", "synonymous"]))

    assert len(sym_2_fn) == 2
    assert sym_2_fn["PLEKHN1"] == 1
    assert sym_2_fn["SAMD11"] == 2


def test_filter_overlapping_events(f1_trio: GenotypeData) -> None:
    overlapping_events = filter_overlapping_events(
        [["SAMD11"], ["SAMD11"], ["PLEKHN1"]], ["SAMD11", "POGZ"],
    )

    assert len(overlapping_events) == 2
    assert overlapping_events == [["SAMD11"], ["SAMD11"]]


def test_overlap_enrichment_result_dict(f1_trio: GenotypeData) -> None:
    events = [["SAMD11"], ["SAMD11"], ["PLEKHN1"]]
    genes = ["PLEKHN1", "POGZ"]

    overlapped = filter_overlapping_events(events, genes)
    assert overlapped == [["PLEKHN1"]]

    enrichment_result = EnrichmentSingleResult(
        "all",
        len(events),
        len(overlapped),
        0.12345,
        0.54321,
    )

    assert (
        str(enrichment_result)
        == "EnrichmentSingleResult(all): events=3; overlapped=1; "
        "expected=0.12345; "
        "pvalue=0.54321"
    )


def test_counter_base_counters() -> None:

    assert len(EVENT_COUNTERS) == 2
    assert isinstance(
        EVENT_COUNTERS["enrichment_events_counting"], EventsCounter)
    assert isinstance(
        EVENT_COUNTERS["enrichment_gene_counting"], GeneEventsCounter)


def test_events_counter(f1_trio: GenotypeData) -> None:
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name)),
    )
    psc = f1_trio.get_person_set_collection("phenotype")
    assert psc is not None
    variant_events = GenotypeHelper.collect_denovo_events(variants)

    # genotype_helper = GenotypeHelper(f1_trio, psc)
    # children_stats = gh.get_children_stats()
    children_by_sex = psc.person_sets["phenotype1"].get_children_by_sex()
    effect_types = set(["missense", "synonymous"])
    event_counter = EventsCounter()
    print(children_by_sex)
    events = event_counter.events(
        variant_events, children_by_sex, effect_types)
    print(events)

    assert events.all is not None
    assert len(events.all) == 2
    assert events.all == [["SAMD11"], ["SAMD11"]]

    assert events.rec is not None
    assert len(events.rec) == 1
    assert events.rec == [["SAMD11"]]

    assert events.male is not None
    assert len(events.male) == 1
    assert events.male == [["SAMD11"]]

    assert events.female is not None
    assert len(events.female) == 1
    assert events.female == [["SAMD11"]]

    assert events.unspecified is not None
    assert len(events.unspecified) == 0


def test_gene_events_counter(f1_trio: GenotypeData) -> None:
    variants = list(
        f1_trio.query_variants(inheritance=str(Inheritance.denovo.name)),
    )
    psc = f1_trio.get_person_set_collection("phenotype")
    assert psc is not None

    # genotype_helper = GenotypeHelper(f1_trio, psc)
    # children_stats = gh.get_children_stats()
    children_by_sex = psc.person_sets["phenotype1"].get_children_by_sex()
    effect_types = set(["missense", "synonymous"])
    event_counter = GeneEventsCounter()

    variant_events = GenotypeHelper.collect_denovo_events(variants)
    events = event_counter.events(
        variant_events, children_by_sex, effect_types)

    assert events.all is not None
    assert len(events.all) == 1
    assert events.all == [["SAMD11"]]

    assert events.rec is not None
    assert len(events.rec) == 1
    assert events.rec == [["SAMD11"]]

    assert events.male is not None
    assert len(events.male) == 1
    assert events.male == [["SAMD11"]]

    assert events.female is not None
    assert len(events.female) == 1
    assert events.female == [["SAMD11"]]
    assert len(events.female) == 1

    assert events.unspecified is not None
    assert len(events.unspecified) == 0
