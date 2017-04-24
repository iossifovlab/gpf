'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.tool import EnrichmentTool
import pytest
from enrichment_tool.background import SamochaBackground
from enrichment_tool.event_counters import EventsCounter, GeneEventsCounter
from enrichment_tool.genotype_helper import GenotypeHelper as GH


@pytest.fixture(scope='module')
def background(request):
    bg = SamochaBackground()
    bg.precompute()
    return bg


def test_enrichment_tool_gene_events(autism_studies,
                                     background, gene_set):
    tool = EnrichmentTool(background, GeneEventsCounter())
    assert tool is not None

    gh = GH.from_studies(autism_studies, 'prb', 'LGDs')

    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants(),
        gh.get_children_stats())
    assert enrichment_results is not None

    print(enrichment_results['all'])
    print(enrichment_results['rec'])
    print(enrichment_results['male'])
    print(enrichment_results['female'])

    er = enrichment_results
    assert 546 == len(er['all'].events)
    assert 39 == len(er['rec'].events)
    assert 458 == len(er['male'].events)
    assert 107 == len(er['female'].events)

    assert 12.54 == pytest.approx(er['all'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['all'].pvalue, abs=1E-2)

    assert 0.90 == pytest.approx(er['rec'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['rec'].pvalue, abs=1E-2)

    assert 10.65 == pytest.approx(er['male'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['male'].pvalue, abs=1E-2)

    assert 1.88 == pytest.approx(er['female'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['female'].pvalue, abs=1E-2)


def test_enrichment_tool_events(autism_studies,
                                background, gene_set):
    tool = EnrichmentTool(background, EventsCounter())
    assert tool is not None

    gh = GH.from_studies(autism_studies, 'prb', 'LGDs')

    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants(),
        gh.get_children_stats())
    assert enrichment_results is not None

    print(enrichment_results['all'])
    print(enrichment_results['rec'])
    print(enrichment_results['male'])
    print(enrichment_results['female'])

    er = enrichment_results

    assert 606 == len(er['all'].events)
    assert 39 == len(er['rec'].events)
    assert 492 == len(er['male'].events)
    assert 114 == len(er['female'].events)

    assert 12.54 == pytest.approx(er['all'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['all'].pvalue, abs=1E-2)

    assert 0.81 == pytest.approx(er['rec'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['rec'].pvalue, abs=1E-2)

    assert 10.65 == pytest.approx(er['male'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['male'].pvalue, abs=1E-2)

    assert 1.89 == pytest.approx(er['female'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['female'].pvalue, abs=1E-2)
