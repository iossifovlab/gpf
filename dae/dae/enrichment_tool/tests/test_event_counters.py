from dae.variants.attributes import Inheritance

from dae.enrichment_tool.event_counters import \
    filter_denovo_one_event_per_family, \
    filter_denovo_one_gene_per_recurrent_events, \
    filter_denovo_one_gene_per_events, get_sym_2_fn, EnrichmentResult, \
    filter_overlapping_events, overlap_enrichment_result_dict, CounterBase, \
    EventsCounter, GeneEventsCounter


def test_filter_denovo_one_event_per_family(f1_trio):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))

    assert len(variants) == 5

    fv = filter_denovo_one_event_per_family(variants)

    assert len(fv) == 3
    assert fv == [['SAMD11'], ['SAMD11'], ['PLEKHN1']]


def test_filter_denovo_one_gene_per_recurrent_events(f1_trio):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))

    assert len(variants) == 5

    fv = filter_denovo_one_gene_per_recurrent_events(variants)

    assert len(fv) == 1
    assert fv == [['SAMD11']]


def test_filter_denovo_one_gene_per_events(f1_trio):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))

    assert len(variants) == 5

    fv = filter_denovo_one_gene_per_events(variants)

    assert len(fv) == 2
    assert fv == [['PLEKHN1'], ['SAMD11']]


def test_get_sym_2_fn(f1_trio):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))

    assert len(variants) == 5

    sym_2_fn = get_sym_2_fn(variants)

    assert len(sym_2_fn) == 2
    assert sym_2_fn['PLEKHN1'] == 1
    assert sym_2_fn['SAMD11'] == 2


def test_filter_overlapping_events(f1_trio):
    oe = filter_overlapping_events(
        [['SAMD11'], ['SAMD11'], ['PLEKHN1']], ['SAMD11', 'POGZ'])

    assert len(oe) == 2
    assert oe == [['SAMD11'], ['SAMD11']]


def test_overlap_enrichment_result_dict(f1_trio):
    enrichment_result = EnrichmentResult('all')
    enrichment_result.events = [['SAMD11'], ['SAMD11'], ['PLEKHN1']]
    enrichment_result.expected = 0.12345
    enrichment_result.pvalue = 0.54321

    enrichment_results = {'all': enrichment_result}

    overlap_enrichment_result_dict(enrichment_results, ['PLEKHN1', 'POGZ'])
    assert len(enrichment_results['all'].overlapped) == 1
    assert enrichment_results['all'].overlapped == [['PLEKHN1']]

    assert str(enrichment_results['all']) == \
        'EnrichmentResult(all): events=3; overlapped=1; ' \
        'expected=0.12345; '\
        'pvalue=0.54321'


def test_counter_base_counters():
    counters = CounterBase.counters()

    assert len(counters) == 2
    assert counters['enrichmentEventsCounting'] == EventsCounter
    assert counters['enrichmentGeneCounting'] == GeneEventsCounter


def test_events_counter(f1_trio):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))
    event_counter = EventsCounter()

    events = event_counter.events(variants)

    assert len(events['all'].events) == 3
    assert events['all'].events == [['SAMD11'], ['SAMD11'], ['PLEKHN1']]
    assert len(events['rec'].events) == 1
    assert events['rec'].events == [['SAMD11']]
    assert len(events['male'].events) == 1
    assert events['male'].events == [['SAMD11']]
    assert len(events['female'].events) == 2
    assert events['female'].events == [['SAMD11'], ['PLEKHN1']]
    assert len(events['unspecified'].events) == 0


def test_gene_events_counter(f1_trio):
    variants = list(f1_trio.query_variants(
        inheritance=str(Inheritance.denovo.name)))
    gene_events_counter = GeneEventsCounter()

    events = gene_events_counter.events(variants)

    assert len(events['all'].events) == 2
    assert events['all'].events == [['PLEKHN1'], ['SAMD11']]
    assert len(events['rec'].events) == 1
    assert events['rec'].events == [['SAMD11']]
    assert len(events['male'].events) == 1
    assert events['male'].events == [['SAMD11']]
    assert len(events['female'].events) == 2
    assert events['female'].events == [['PLEKHN1'], ['SAMD11']]
    assert len(events['unspecified'].events) == 0
