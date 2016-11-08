'''
Created on Nov 7, 2016

@author: lubo
'''
import numpy as np

import pytest
from enrichment_tool.background import SynonymousBackground
from enrichment_tool.event_counters import GeneEventsCounter


@pytest.fixture(scope='module')
def background(request):
    bg = SynonymousBackground()
    bg.precompute()
    return bg


def test_synonymous_background_stats_default(background):
    assert background is not None

    assert 211645 == np.sum(background.background['raw'])


def test_stats_autism_lgd(background, denovo_studies,
                          gene_set, children_stats):
    counter = GeneEventsCounter('autism', 'LGDs')
    events = counter.events(denovo_studies)

    stats = background.calc_stats(
        events,
        gene_set,
        children_stats['autism'])

    assert stats is not None

    assert 17.7123 == pytest.approx(stats.all_expected, 2)
    assert 8.3E-05 == pytest.approx(stats.all_pvalue, 4)

    assert 1.265169 == pytest.approx(stats.rec_expected, 2)
    assert 3.5E-06 == pytest.approx(stats.rec_pvalue, 4)

    assert 14.85763 == pytest.approx(stats.male_expected, 2)
    assert 0.0021 == pytest.approx(stats.male_pvalue, 4)

    assert 3.47 == pytest.approx(stats.female_expected, 2)
    assert 4.6E-05 == pytest.approx(stats.female_pvalue, 4)


def test_stats_schizophrenia_with_lgd(background, denovo_studies,
                                      gene_set, children_stats):
    counter = GeneEventsCounter('schizophrenia', 'LGDs')
    events = counter.events(denovo_studies)

    stats = background.calc_stats(
        events,
        gene_set,
        children_stats['schizophrenia'])

    assert stats is not None

    assert 3.02 == pytest.approx(stats.all_expected, 2)
    assert 0.128851 == pytest.approx(stats.all_pvalue, 4)

    assert 0.06 == pytest.approx(stats.rec_expected, 2)
    assert 1 == pytest.approx(stats.rec_pvalue, 4)

    assert 1.56 == pytest.approx(stats.male_expected, 2)
    assert 0.0698 == pytest.approx(stats.male_pvalue, 4)

    assert 1.46 == pytest.approx(stats.female_expected, 2)
    assert 0.6579 == pytest.approx(stats.female_pvalue, 4)


def test_stats_unaffected_with_missense(background, denovo_studies,
                                        gene_set, children_stats):
    counter = GeneEventsCounter('unaffected', 'missense')
    events = counter.events(denovo_studies)

    stats = background.calc_stats(
        events,
        gene_set,
        children_stats['unaffected'])

    assert stats is not None

    assert 43.924 == pytest.approx(stats.all_expected, 2)
    assert 0.81817466 == pytest.approx(stats.all_pvalue, 4)

    assert 3.665747 == pytest.approx(stats.rec_expected, 2)
    assert 0.7875 == pytest.approx(stats.rec_pvalue, 4)

    assert 20.69687 == pytest.approx(stats.male_expected, 2)
    assert 0.8228654 == pytest.approx(stats.male_pvalue, 4)

    assert 25.368269 == pytest.approx(stats.female_expected, 2)
    assert 0.47852 == pytest.approx(stats.female_pvalue, 4)
