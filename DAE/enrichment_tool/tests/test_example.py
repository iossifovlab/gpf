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

    autism_studes = [
        st for st in denovo_studies
        if 'autism' == st.get_attr('study.phenotype')]

    # create background
    background = SamochaBackground()

    # create enrichment tool
    tool = EnrichmentTool(background, GeneEventsCounter())

    # load gene set
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['chromatin modifiers'].keys()

    events, overlapped, stats = tool.calc(
        autism_studes,
        'prb',
        'LGDs',
        gene_set)
    print(events)
    print(overlapped)
    print(stats)

    events, overlapped, stats = tool.calc(
        denovo_studies,
        'sib',
        'LGDs',
        gene_set)
    print(events)
    print(overlapped)
    print(stats)
