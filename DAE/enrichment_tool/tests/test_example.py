'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.background import SamochaBackground
from DAE import get_gene_sets_symNS, vDB
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.event_counters import GeneEventsCounter


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
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['chromatin modifiers'].keys()

    # create enrichment tool
    tool = EnrichmentTool(background, GeneEventsCounter())

    enrichment_results = tool.calc(
        autism_studies,
        'prb',
        'LGDs',
        gene_set)
    print(enrichment_results['all'])
    print(enrichment_results['rec'])
    print(enrichment_results['male'])
    print(enrichment_results['female'])

    enrichment_results = tool.calc(
        denovo_studies,
        'sib',
        'LGDs',
        gene_set)
    print(enrichment_results['all'])
    print(enrichment_results['rec'])
    print(enrichment_results['male'])
    print(enrichment_results['female'])
