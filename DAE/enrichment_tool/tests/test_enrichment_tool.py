'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.tool import EnrichmentTool
import pytest
from enrichment_tool.background import SamochaBackground
from enrichment_tool.event_counters import EventsCounter, GeneEventsCounter


@pytest.fixture(scope='module')
def background(request):
    bg = SamochaBackground()
    bg.precompute()
    return bg


def test_enrichment_tool_gene_events(denovo_studies, children_stats,
                                     background, gene_set):
    tool = EnrichmentTool(denovo_studies, children_stats,
                          background, GeneEventsCounter)
    assert tool is not None

    events, overlapped, stats = tool.calc('autism', 'LGDs', gene_set)
    assert events is not None
    assert stats is not None

    print(events)
    print(overlapped)
    print(stats)

    assert 546 == len(events.all_events)
    assert 39 == len(events.rec_events)
    assert 458 == len(events.male_events)
    assert 107 == len(events.female_events)

    assert 12.54 == pytest.approx(stats.all_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.all_pvalue, abs=1E-2)

    assert 0.90 == pytest.approx(stats.rec_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.rec_pvalue, abs=1E-2)

    assert 10.65 == pytest.approx(stats.male_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.male_pvalue, abs=1E-2)

    assert 1.88 == pytest.approx(stats.female_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.female_pvalue, abs=1E-2)


def test_enrichment_tool_events(denovo_studies, children_stats,
                                background, gene_set):
    tool = EnrichmentTool(denovo_studies, children_stats,
                          background, EventsCounter)
    assert tool is not None

    events, overlapped, stats = tool.calc('autism', 'LGDs', gene_set)
    assert events is not None
    assert stats is not None

    print(events)
    print(overlapped)
    print(stats)

    assert 606 == len(events.all_events)
    assert 39 == len(events.rec_events)
    assert 492 == len(events.male_events)
    assert 114 == len(events.female_events)

    assert 12.54 == pytest.approx(stats.all_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.all_pvalue, abs=1E-2)

    assert 0.81 == pytest.approx(stats.rec_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.rec_pvalue, abs=1E-2)

    assert 10.65 == pytest.approx(stats.male_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.male_pvalue, abs=1E-2)

    assert 1.89 == pytest.approx(stats.female_expected, abs=1E-2)
    assert 0.0 == pytest.approx(stats.female_pvalue, abs=1E-2)
