'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from enrichment_tool.background import SamochaBackground
from enrichment_tool.event_counters import GeneEventsCounter
from enrichment_tool.config import children_stats_counter


@pytest.fixture(scope='module')
def background(request):
    bg = SamochaBackground()
    bg.precompute()
    return bg


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

    assert 12.5358 == pytest.approx(stats.all_expected, abs=1E-4)
    assert 0.0 == pytest.approx(stats.all_pvalue, abs=1E-4)

    assert 0.89924 == pytest.approx(stats.rec_expected, abs=1E-4)
    assert 0.0 == pytest.approx(stats.rec_pvalue, abs=1E-4)

    assert 10.65059 == pytest.approx(stats.male_expected, abs=1E-4)
    assert 0.0 == pytest.approx(stats.male_pvalue, abs=1E-4)

    assert 1.8853 == pytest.approx(stats.female_expected, abs=1E-4)
    assert 0.0 == pytest.approx(stats.female_pvalue, abs=1E-4)
