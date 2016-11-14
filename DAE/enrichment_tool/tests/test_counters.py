'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest

from enrichment_tool.event_counters import CounterBase, EventsCounter,\
    GeneEventsCounter


def test_variants_unaffected_with_effect_type_lgd(denovo_studies):
    counter = CounterBase()

    variants = counter.get_variants(
        denovo_studies.get_studies('unaffected'),
        'sib',
        'LGDs')
    assert variants is not None

    count = 0
    for v in variants:
        assert 'sib' in v.inChS
        count += 1
    print(count)
    assert 243 == count


def test_variants_unaffected_with_effect_type_missense(denovo_studies):
    counter = CounterBase()

    variants = counter.get_variants(
        denovo_studies.get_studies('unaffected'),
        'sib',
        'missense')
    assert variants is not None

    count = 0
    for v in variants:
        assert 'sib' in v.inChS
        assert 'missense' == v.requestedGeneEffects[0]['eff']
        count += 1
    print(count)
    assert 1616 == count


def test_variants_unaffected_with_effect_type_synonimous(denovo_studies):
    counter = CounterBase()

    variants = counter.get_variants(
        denovo_studies.get_studies('unaffected'),
        'sib',
        'synonymous')
    assert variants is not None

    count = 0
    for v in variants:
        assert 'sib' in v.inChS
        assert 'synonymous' == v.requestedGeneEffects[0]['eff']
        count += 1
    print(count)
    assert 686 == count


def test_variants_autism_with_effect_type_lgd(denovo_studies):
    counter = CounterBase()

    variants = counter.get_variants(
        denovo_studies.get_studies('autism'),
        'prb',
        'LGDs')
    assert variants is not None

    count = 0
    for v in variants:
        assert 'prb' in v.inChS
        count += 1
    print(count)
    assert 607 == count


def test_events_not_implemented(denovo_studies):
    counter = CounterBase()

    with pytest.raises(NotImplementedError):
        counter.events(
            denovo_studies.get_studies('autism'),
            'prb',
            'LGDs')


def test_events_autism_with_effect_type_lgd(denovo_studies):
    counter = EventsCounter()

    events = counter.events(
        denovo_studies.get_studies('autism'),
        'prb',
        'LGDs')
    assert events is not None

    assert 606 == len(events.all_events)
    assert 39 == len(events.rec_events)
    assert 492 == len(events.male_events)
    assert 114 == len(events.female_events)


def test_events_unaffected_with_effect_type_lgd(denovo_studies):
    counter = EventsCounter()

    events = counter.events(
        denovo_studies.get_studies('unaffected'),
        'sib',
        'LGDs')
    assert events is not None

    assert 224 == len(events.all_events)
    assert 5 == len(events.rec_events)
    assert 113 == len(events.male_events)
    assert 111 == len(events.female_events)


def test_events_schizophrenia_with_effect_type_lgd(denovo_studies):
    counter = EventsCounter()

    events = counter.events(
        denovo_studies.get_studies('schizophrenia'),
        'prb',
        'LGDs')

    assert events is not None

    assert 95 == len(events.all_events)
    assert 2 == len(events.rec_events)
    assert 49 == len(events.male_events)
    assert 46 == len(events.female_events)


def test_overlapped_events_autism_with_effect_type_lgd(
        denovo_studies, gene_set):

    counter = EventsCounter()

    events = counter.events(
        denovo_studies.get_studies('autism'),
        'prb',
        'LGDs')
    overlapped_events = events.overlap(gene_set)

    assert overlapped_events is not None

    assert 56 == len(overlapped_events.all_events)
    assert 9 == len(overlapped_events.rec_events)
    assert 40 == len(overlapped_events.male_events)
    assert 16 == len(overlapped_events.female_events)


def test_overlapped_events_unaffected_with_effect_type_synonymous(
        denovo_studies, gene_set):
    counter = EventsCounter()

    events = counter.events(
        denovo_studies.get_studies('unaffected'),
        'sib',
        'synonymous')
    overlapped_events = events.overlap(gene_set)

    assert overlapped_events is not None

    assert 18 == len(overlapped_events.all_events)
    assert 1 == len(overlapped_events.rec_events)
    assert 14 == len(overlapped_events.male_events)
    assert 4 == len(overlapped_events.female_events)


def test_overlapped_events_schizophrenia_with_effect_type_missense(
        denovo_studies, gene_set):
    counter = EventsCounter()

    events = counter.events(
        denovo_studies.get_studies('schizophrenia'),
        'prb',
        'missense')
    overlapped_events = events.overlap(gene_set)

    assert overlapped_events is not None

    assert 23 == len(overlapped_events.all_events)
    assert 2 == len(overlapped_events.rec_events)
    assert 10 == len(overlapped_events.male_events)
    assert 13 == len(overlapped_events.female_events)


def test_gene_events_autism_with_effect_type_lgd(denovo_studies):
    counter = GeneEventsCounter()

    events = counter.events(
        denovo_studies.get_studies('autism'),
        'prb',
        'LGDs')

    assert events is not None

    assert 546 == len(events.all_events)
    assert 39 == len(events.rec_events)
    assert 458 == len(events.male_events)
    assert 107 == len(events.female_events)


def test_gene_events_unaffected_with_effect_type_lgd(denovo_studies):
    counter = GeneEventsCounter()

    events = counter.events(
        denovo_studies.get_studies('unaffected'),
        'sib',
        'LGDs')
    assert events is not None

    assert 220 == len(events.all_events)
    assert 5 == len(events.rec_events)
    assert 113 == len(events.male_events)
    assert 111 == len(events.female_events)


def test_gene_events_schizophrenia_with_effect_type_lgd(denovo_studies):
    counter = GeneEventsCounter()

    events = counter.events(
        denovo_studies.get_studies('schizophrenia'),
        'prb',
        'LGDs')
    assert events is not None

    assert 93 == len(events.all_events)
    assert 2 == len(events.rec_events)
    assert 48 == len(events.male_events)
    assert 45 == len(events.female_events)


def test_overlapped_gene_events_autism_with_effect_type_lgd(
        denovo_studies, gene_set):
    counter = GeneEventsCounter()

    events = counter.events(
        denovo_studies.get_studies('autism'),
        'prb',
        'LGDs')
    overlapped_events = events.overlap(gene_set)

    assert overlapped_events is not None

    assert 36 == len(overlapped_events.all_events)
    assert 9 == len(overlapped_events.rec_events)
    assert 28 == len(overlapped_events.male_events)
    assert 13 == len(overlapped_events.female_events)


def test_overlapped_gene_events_unaffected_with_effect_type_synonymous(
        denovo_studies, gene_set):
    counter = GeneEventsCounter()

    events = counter.events(
        denovo_studies.get_studies('unaffected'),
        'sib',
        'synonymous')
    overlapped_events = events.overlap(gene_set)

    assert overlapped_events is not None

    assert 17 == len(overlapped_events.all_events)
    assert 1 == len(overlapped_events.rec_events)
    assert 13 == len(overlapped_events.male_events)
    assert 4 == len(overlapped_events.female_events)


def test_overlapped_gene_events_schizophrenia_with_effect_type_missense(
        denovo_studies, gene_set):
    counter = GeneEventsCounter()

    events = counter.events(
        denovo_studies.get_studies('schizophrenia'),
        'prb',
        'missense')
    overlapped_events = events.overlap(gene_set)

    assert overlapped_events is not None

    assert 21 == len(overlapped_events.all_events)
    assert 2 == len(overlapped_events.rec_events)
    assert 9 == len(overlapped_events.male_events)
    assert 12 == len(overlapped_events.female_events)
