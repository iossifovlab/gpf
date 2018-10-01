'''
Created on Nov 8, 2016

@author: lubo
'''
from __future__ import unicode_literals
from enrichment_tool.tool import EnrichmentTool
import pytest
from enrichment_tool.event_counters import EventsCounter, GeneEventsCounter
from enrichment_tool.genotype_helper import GenotypeHelper as GH
from pheno.common import Role


def test_enrichment_tool_gene_events(autism_studies,
                                     samocha_background, gene_set):
    tool = EnrichmentTool(samocha_background, GeneEventsCounter())
    assert tool is not None

    gh = GH.from_studies(autism_studies, Role.prb)

    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants('LGDs'),
        gh.get_children_stats())
    assert enrichment_results is not None

    er = enrichment_results
    # assert 546 == len(er['all'].events) FIXME: changed after reannotation
    assert 551 == len(er['all'].events)
    assert 39 == len(er['rec'].events)
    # assert 458 == len(er['male'].events)
    assert 462 == len(er['male'].events)
    # assert 107 == len(er['female'].events)
    assert 108 == len(er['female'].events)

    assert 12.54 == pytest.approx(er['all'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['all'].pvalue, abs=1E-2)

    assert 0.90 == pytest.approx(er['rec'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['rec'].pvalue, abs=1E-2)

    assert 10.65 == pytest.approx(er['male'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['male'].pvalue, abs=1E-2)

    assert 1.88 == pytest.approx(er['female'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['female'].pvalue, abs=1E-2)


def test_enrichment_tool_events(autism_studies,
                                samocha_background, gene_set):
    tool = EnrichmentTool(samocha_background, EventsCounter())
    assert tool is not None

    gh = GH.from_studies(autism_studies, Role.prb)

    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants('LGDs'),
        gh.get_children_stats())
    assert enrichment_results is not None

    er = enrichment_results

    # assert 606 == len(er['all'].events) FIXME: changed after reannotation
    assert 611 == len(er['all'].events)
    assert 39 == len(er['rec'].events)
    # assert 492 == len(er['male'].events)
    assert 496 == len(er['male'].events)
    # assert 114 == len(er['female'].events)
    assert 115 == len(er['female'].events)

    assert 12.54 == pytest.approx(er['all'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['all'].pvalue, abs=1E-2)

    assert 0.81 == pytest.approx(er['rec'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['rec'].pvalue, abs=1E-2)

    assert 10.65 == pytest.approx(er['male'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['male'].pvalue, abs=1E-2)

    assert 1.89 == pytest.approx(er['female'].expected, abs=1E-2)
    assert 0.0 == pytest.approx(er['female'].pvalue, abs=1E-2)
