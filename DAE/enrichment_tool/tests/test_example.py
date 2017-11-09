'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.background import SamochaBackground
from DAE import vDB
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.event_counters import GeneEventsCounter
from enrichment_tool.genotype_helper import GenotypeHelper as GH
from gene.gene_set_collections import GeneSetsCollection


def test_simple_example():
    # load WE denovo studies
    studies = vDB.get_studies('ALL WHOLE EXOME')
    denovo_studies = [
        st for st in studies if 'WE' == st.get_attr('study.type')]

    autism_studies = [
        st for st in denovo_studies
        if 'autism' == st.get_attr('study.phenotype')]

    # create background
    background = SamochaBackground()

    # load a gene set
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_set = gsc.get_gene_set('chromatin modifiers')

    # create enrichment tool
    tool = EnrichmentTool(background, GeneEventsCounter())

    gh = GH.from_studies(autism_studies, 'prb')
    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants('LGDs'),
        gh.get_children_stats())

    gh = GH.from_studies(autism_studies, 'sib')
    enrichment_results = tool.calc(
        'LGDs',
        gene_set,
        gh.get_variants('LGDs'),
        gh.get_children_stats())
