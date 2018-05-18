'''
Created on Mar 16, 2018

@author: lubo
'''
from __future__ import unicode_literals
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.event_counters import GeneEventsCounter
from enrichment_tool.genotype_helper import GenotypeHelper as GH


def test_enrichment_tool_gene_events_autism(
        denovo_db, samocha_background, gene_set):
    tool = EnrichmentTool(samocha_background, GeneEventsCounter())
    assert tool is not None

    # gh = GH.from_studies(autism_studies, 'prb')
    gh = GH.from_dataset(denovo_db, 'phenotype', 'autism')

    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants('LGDs'),
        gh.get_children_stats())
    assert enrichment_results is not None

    er = enrichment_results
    assert 78 == len(er['all'].events)
    assert 8 == len(er['rec'].events)
    assert 0 == len(er['male'].events)
    assert 0 == len(er['female'].events)
    assert 78 == len(er['unspecified'].events)


def test_enrichment_tool_gene_events_cantu_syndrome(
        denovo_db, samocha_background, gene_set):
    tool = EnrichmentTool(samocha_background, GeneEventsCounter())
    assert tool is not None

    # gh = GH.from_studies(autism_studies, 'prb')
    gh = GH.from_dataset(denovo_db, 'phenotype', 'cantu_syndrome')

    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants('LGDs'),
        gh.get_children_stats())
    assert enrichment_results is not None

    er = enrichment_results
    assert 0 == len(er['all'].events)
    assert 0 == len(er['rec'].events)
    assert 0 == len(er['male'].events)
    assert 0 == len(er['female'].events)
    assert 0 == len(er['unspecified'].events)
