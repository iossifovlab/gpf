'''
Created on Nov 7, 2016

@author: lubo
'''
import numpy as np

import pytest
from enrichment_tool.background import SynonymousBackground
from enrichment_tool.event_counters import GeneEventsCounter
from enrichment_tool.config import children_stats_counter


@pytest.fixture(scope='module')
def background(request):
    bg = SynonymousBackground(use_cache=True)
    return bg


# def test_synonymous_background_default(background):
#     assert background.background is not None
#     assert background.foreground is not None
#
#     background.cache_save()
#
#     b1 = SynonymousBackground()
#     assert b1.cache_load()
#     assert b1.background is not None
#     assert b1.foreground is not None
#
#     assert np.all(background.background == b1.background)
#     assert np.all(background.foreground == b1.foreground)
#
#
# def test_cache_clear(background):
#     background.cache_clear()
#     background.cache_clear()
#
#     assert not background.cache_load()


def test_synonymous_background_stats_default(background):
    assert background is not None

    assert 211645 == np.sum(background.background['raw'])


def test_stats_autism_lgd(background, autism_studies,
                          gene_set):
    counter = GeneEventsCounter()
    events = counter.events(
        autism_studies, 'prb', 'LGDs')

    children_stats = children_stats_counter(autism_studies, 'prb')
    _, stats = background.calc_stats(
        'LGDs',
        events,
        gene_set,
        children_stats)

    assert stats is not None

    assert 17.71 == pytest.approx(stats.all_expected, abs=1E-2)
    assert 8.3E-05 == pytest.approx(stats.all_pvalue, abs=1E-4)

    assert 1.27 == pytest.approx(stats.rec_expected, abs=1E-2)
    assert 3.5E-06 == pytest.approx(stats.rec_pvalue, abs=1E-4)

    assert 14.86 == pytest.approx(stats.male_expected, abs=1E-2)
    assert 0.0021 == pytest.approx(stats.male_pvalue, abs=1E-4)

    assert 3.47 == pytest.approx(stats.female_expected, abs=1E-2)
    assert 4.6E-05 == pytest.approx(stats.female_pvalue, abs=1E-4)


def test_stats_schizophrenia_with_lgd(background, schizophrenia_studies,
                                      gene_set):
    counter = GeneEventsCounter()
    events = counter.events(schizophrenia_studies,
                            'prb', 'LGDs')
    children_stats = children_stats_counter(schizophrenia_studies, 'prb')

    _, stats = background.calc_stats(
        'LGDs',
        events,
        gene_set,
        children_stats)

    assert stats is not None

    assert 3.02 == pytest.approx(stats.all_expected, abs=1E-2)
    assert 0.128851 == pytest.approx(stats.all_pvalue, abs=1E-4)

    assert 0.06 == pytest.approx(stats.rec_expected, abs=1E-2)
    assert 1 == pytest.approx(stats.rec_pvalue, abs=1E-4)

    assert 1.56 == pytest.approx(stats.male_expected, abs=1E-2)
    assert 0.0698 == pytest.approx(stats.male_pvalue, abs=1E-4)

    assert 1.46 == pytest.approx(stats.female_expected, abs=1E-2)
    assert 0.6579 == pytest.approx(stats.female_pvalue, abs=1E-4)


def test_stats_unaffected_with_missense(background, unaffected_studies,
                                        gene_set):
    counter = GeneEventsCounter()
    events = counter.events(
        unaffected_studies, 'sib', 'missense')
    children_stats = children_stats_counter(unaffected_studies, 'sib')

    _, stats = background.calc_stats(
        'missense',
        events,
        gene_set,
        children_stats)

    assert stats is not None

    assert 43.924 == pytest.approx(stats.all_expected, abs=1E-2)
    assert 0.81817466 == pytest.approx(stats.all_pvalue, abs=1E-4)

    assert 3.665747 == pytest.approx(stats.rec_expected, abs=1E-2)
    assert 0.7875 == pytest.approx(stats.rec_pvalue, abs=1E-4)

    assert 20.69687 == pytest.approx(stats.male_expected, abs=1E-2)
    assert 0.8228654 == pytest.approx(stats.male_pvalue, abs=1E-4)

    assert 25.368269 == pytest.approx(stats.female_expected, abs=1E-2)
    assert 0.47852 == pytest.approx(stats.female_pvalue, abs=1E-4)
