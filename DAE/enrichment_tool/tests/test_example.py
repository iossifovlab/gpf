'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.background import SamochaBackground
from enrichment_tool.config import DenovoStudies, ChildrenStats
from DAE import get_gene_sets_symNS
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.event_counters import GeneEventsCounter


def test_simple_example():
    # create background
    background = SamochaBackground()
    background.precompute()

    # enrichment denovo studies helper
    denovo_studies = DenovoStudies()

    # collect children stats from denovo studies
    children_stats = ChildrenStats.build(denovo_studies)

    # create enrichment tool
    tool = EnrichmentTool(
        denovo_studies, children_stats, background, GeneEventsCounter)

    # load gene set
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['chromatin modifiers'].keys()

    events, overlapped, stats = tool.calc('autism', 'LGDs', gene_set)
    print(events)
    print(overlapped)
    print(stats)

    events, overlapped, stats = tool.calc(
        'unaffected', 'LGDs', gene_set)
    print(events)
    print(overlapped)
    print(stats)
