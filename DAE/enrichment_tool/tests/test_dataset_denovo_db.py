'''
Created on Mar 15, 2018

@author: lubo
'''
from __future__ import unicode_literals
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.genotype_helper import GenotypeHelper as GH
from enrichment_tool.event_counters import GeneEventsCounter, EventsCounter


def test_enrichment_tool_gene_events(denovo_db,
                                     synonymous_background, gene_set):
    tool = EnrichmentTool(synonymous_background, GeneEventsCounter())
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


def test_enrichment_tool_events(denovo_db,
                                synonymous_background, gene_set):
    tool = EnrichmentTool(synonymous_background, EventsCounter())
    assert tool is not None

    gh = GH.from_dataset(denovo_db, 'phenotype', 'autism')
    # gh = GH.from_studies(autism_studies, 'prb')

    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants('LGDs'),
        gh.get_children_stats())
    assert enrichment_results is not None

    er = enrichment_results

    assert 93 == len(er['all'].events)
    assert 8 == len(er['rec'].events)
    assert 0 == len(er['male'].events)
    assert 0 == len(er['female'].events)
    assert 93 == len(er['unspecified'].events)
