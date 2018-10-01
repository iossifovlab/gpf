'''
Created on Nov 8, 2016

@author: lubo
'''
from __future__ import unicode_literals
from enrichment_tool.event_counters import EventsCounter,\
    GeneEventsCounter, overlap_enrichment_result_dict
from enrichment_tool.genotype_helper import GenotypeHelper as GH
from pheno.common import Role


def test_variants_unaffected_with_effect_type_lgd(unaffected_studies):
    gh = GH.from_studies(unaffected_studies, Role.sib)

    variants = gh.get_variants('LGDs')
    assert variants is not None

    count = 0
    for v in variants:
        assert Role.sib.name in v.inChS
        count += 1
    assert 232 == count


def test_variants_unaffected_with_effect_type_missense(unaffected_studies):
    gh = GH.from_studies(unaffected_studies, Role.sib)

    variants = gh.get_variants('missense')
    assert variants is not None

    count = 0
    for v in variants:
        assert Role.sib.name in v.inChS
        assert 'missense' == v.requestedGeneEffects[0]['eff']
        count += 1
    assert 1482 == count


def test_variants_unaffected_with_effect_type_synonimous(unaffected_studies):
    gh = GH.from_studies(unaffected_studies, Role.sib)

    variants = gh.get_variants('synonymous')
    assert variants is not None

    count = 0
    for v in variants:
        assert Role.sib.name in v.inChS
        assert 'synonymous' == v.requestedGeneEffects[0]['eff']
        count += 1
    assert 627 == count


def test_variants_autism_with_effect_type_lgd(autism_studies):
    gh = GH.from_studies(autism_studies, Role.prb)

    variants = gh.get_variants('LGDs')
    assert variants is not None

    count = 0
    for v in variants:
        assert Role.prb.name in v.inChS
        count += 1
    # assert 607 == count FIXME: changed after reannotation
    assert 612 == count


def test_events_autism_with_effect_type_lgd(autism_studies):
    counter = EventsCounter()
    gh = GH.from_studies(autism_studies, Role.prb)

    result = counter.events(gh.get_variants('LGDs'))
    assert result is not None

    # assert 606 == len(result['all'].events) FIXME: changed after reannotation
    assert 611 == len(result['all'].events)
    assert 39 == len(result['rec'].events)
    # assert 492 == len(result['male'].events)
    assert 496 == len(result['male'].events)
    # assert 114 == len(result['female'].events)
    assert 115 == len(result['female'].events)


def test_events_unaffected_with_effect_type_lgd(unaffected_studies):
    gh = GH.from_studies(unaffected_studies, Role.sib)

    counter = EventsCounter()
    result = counter.events(gh.get_variants('LGDs'))
    assert result is not None

    assert 224 == len(result['all'].events)
    assert 5 == len(result['rec'].events)
    assert 113 == len(result['male'].events)
    assert 111 == len(result['female'].events)


def test_events_schizophrenia_with_effect_type_lgd(schizophrenia_studies):
    gh = GH.from_studies(schizophrenia_studies, Role.prb)
    counter = EventsCounter()

    result = counter.events(gh.get_variants('LGDs'))

    assert result is not None

    # assert 95 == len(result['all'].events) FIXME: changed after reannotation
    assert 94 == len(result['all'].events)
    assert 2 == len(result['rec'].events)
    # assert 49 == len(result['male'].events)
    assert 48 == len(result['male'].events)
    assert 46 == len(result['female'].events)


def test_overlapped_events_autism_with_effect_type_lgd(
        autism_studies, gene_set):

    gh = GH.from_studies(autism_studies, Role.prb)
    counter = EventsCounter()

    result = counter.events(gh.get_variants('LGDs'))

    overlapped_events = overlap_enrichment_result_dict(result, gene_set)
    assert overlapped_events is not None

    # assert 56 == len(result['all'].overlapped) FIXME: changed after reannotation
    assert 57 == len(result['all'].overlapped)
    assert 9 == len(result['rec'].overlapped)
    # assert 40 == len(result['male'].overlapped)
    assert 41 == len(result['male'].overlapped)
    assert 16 == len(result['female'].overlapped)


def test_overlapped_events_unaffected_with_effect_type_synonymous(
        unaffected_studies, gene_set):

    gh = GH.from_studies(unaffected_studies, Role.sib)

    counter = EventsCounter()

    result = counter.events(gh.get_variants('synonymous'))

    overlapped_events = overlap_enrichment_result_dict(result, gene_set)
    assert overlapped_events is not None

    assert 18 == len(result['all'].overlapped)
    assert 1 == len(result['rec'].overlapped)
    assert 14 == len(result['male'].overlapped)
    assert 4 == len(result['female'].overlapped)


def test_overlapped_events_schizophrenia_with_effect_type_missense(
        schizophrenia_studies, gene_set):
    gh = GH.from_studies(schizophrenia_studies, Role.prb)

    counter = EventsCounter()

    result = counter.events(gh.get_variants('missense'))

    overlapped_events = overlap_enrichment_result_dict(result, gene_set)
    assert overlapped_events is not None

    assert 23 == len(result['all'].overlapped)
    assert 2 == len(result['rec'].overlapped)
    assert 10 == len(result['male'].overlapped)
    assert 13 == len(result['female'].overlapped)


def test_gene_events_autism_with_effect_type_lgd(autism_studies):
    gh = GH.from_studies(autism_studies, Role.prb)

    counter = GeneEventsCounter()

    result = counter.events(gh.get_variants('LGDs'))

    # assert 546 == len(result['all'].events) FIXME: changed after reannotation
    assert 551 == len(result['all'].events)
    assert 39 == len(result['rec'].events)
    # assert 458 == len(result['male'].events)
    assert 462 == len(result['male'].events)
    # assert 107 == len(result['female'].events)
    assert 108 == len(result['female'].events)


def test_gene_events_unaffected_with_effect_type_lgd(unaffected_studies):
    gh = GH.from_studies(unaffected_studies, Role.sib)

    counter = GeneEventsCounter()

    result = counter.events(gh.get_variants('LGDs'))

    assert 220 == len(result['all'].events)
    assert 5 == len(result['rec'].events)
    assert 113 == len(result['male'].events)
    assert 111 == len(result['female'].events)


def test_gene_events_schizophrenia_with_effect_type_lgd(schizophrenia_studies):
    gh = GH.from_studies(schizophrenia_studies, Role.prb)

    counter = GeneEventsCounter()

    result = counter.events(gh.get_variants('LGDs'))

    # assert 93 == len(result['all'].events) FIXME: changed after reannotation
    assert 92 == len(result['all'].events)
    assert 2 == len(result['rec'].events)
    # assert 48 == len(result['male'].events)
    assert 47 == len(result['male'].events)
    assert 45 == len(result['female'].events)


def test_overlapped_gene_events_autism_with_effect_type_lgd(
        autism_studies, gene_set):
    gh = GH.from_studies(autism_studies, Role.prb)
    counter = GeneEventsCounter()

    result = counter.events(gh.get_variants('LGDs'))

    overlapped_events = overlap_enrichment_result_dict(result, gene_set)
    assert overlapped_events is not None

    # assert 36 == len(result['all'].overlapped) FIXME: changed after reannotation
    assert 37 == len(result['all'].overlapped)
    assert 9 == len(result['rec'].overlapped)
    # assert 28 == len(result['male'].overlapped)
    assert 29 == len(result['male'].overlapped)
    assert 13 == len(result['female'].overlapped)


def test_overlapped_gene_events_unaffected_with_effect_type_synonymous(
        unaffected_studies, gene_set):
    gh = GH.from_studies(unaffected_studies, Role.sib)
    counter = GeneEventsCounter()

    result = counter.events(gh.get_variants('synonymous'))

    overlapped_events = overlap_enrichment_result_dict(result, gene_set)
    assert overlapped_events is not None

    assert 17 == len(result['all'].overlapped)
    assert 1 == len(result['rec'].overlapped)
    assert 13 == len(result['male'].overlapped)
    assert 4 == len(result['female'].overlapped)


def test_overlapped_gene_events_schizophrenia_with_effect_type_missense(
        schizophrenia_studies, gene_set):
    gh = GH.from_studies(schizophrenia_studies, Role.prb)
    counter = GeneEventsCounter()

    result = counter.events(gh.get_variants('missense'))

    overlapped_events = overlap_enrichment_result_dict(result, gene_set)
    assert overlapped_events is not None

    assert 21 == len(result['all'].overlapped)
    assert 2 == len(result['rec'].overlapped)
    assert 9 == len(result['male'].overlapped)
    assert 12 == len(result['female'].overlapped)
