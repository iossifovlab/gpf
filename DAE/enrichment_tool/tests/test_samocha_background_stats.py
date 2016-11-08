'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from enrichment_tool.background import SamochaBackground
from enrichment_tool.event_counters import GeneEventsCounter


@pytest.fixture(scope='module')
def background(request):
    bg = SamochaBackground()
    bg.precompute()
    return bg


def test_stats_autism_lgd(background, denovo_studies,
                          gene_set, children_stats):
    counter = GeneEventsCounter('autism', 'LGDs')
    events = counter.events(denovo_studies)

    _, stats = background.calc_stats(
        events,
        gene_set,
        children_stats['autism'])

    assert stats is not None

    assert 12.5358 == pytest.approx(stats.all_expected, 2)
    assert 0.0 == pytest.approx(stats.all_pvalue, 4)

    assert 0.89924 == pytest.approx(stats.rec_expected, 2)
    assert 0.0 == pytest.approx(stats.rec_pvalue, 4)

    assert 10.65059 == pytest.approx(stats.male_expected, 2)
    assert 0.0 == pytest.approx(stats.male_pvalue, 4)

    assert 1.8831 == pytest.approx(stats.female_expected, 2)
    assert 2E-07 == pytest.approx(stats.female_pvalue, 4)
