'''
Created on Nov 8, 2016

@author: lubo
'''
from __future__ import unicode_literals
import pytest
from enrichment_tool.background import SamochaBackground
from enrichment_tool.event_counters import GeneEventsCounter
from enrichment_tool.genotype_helper import GenotypeHelper as GH
from pheno.common import Role


@pytest.fixture(scope='module')
def background(request):
    bg = SamochaBackground()
    return bg


def test_stats_autism_lgd(background, autism_studies,
                          gene_set):
    counter = GeneEventsCounter()
    gh = GH.from_studies(autism_studies, Role.prb)
    variants = gh.get_variants('LGDs')
    children_stats = gh.get_children_stats()

    results = counter.events(variants)

    enrichment_results = background.calc_stats(
        'LGDs',
        results,
        gene_set,
        children_stats)

    assert enrichment_results is not None

    assert 12.5358 == pytest.approx(results['all'].expected, abs=1E-4)
    assert 0.0 == pytest.approx(results['all'].pvalue, abs=1E-4)

    assert 0.89924 == pytest.approx(results['rec'].expected, abs=1E-4)
    assert 0.0 == pytest.approx(results['rec'].pvalue, abs=1E-4)

    assert 10.65059 == pytest.approx(results['male'].expected, abs=1E-4)
    assert 0.0 == pytest.approx(results['male'].pvalue, abs=1E-4)

    assert 1.8853 == pytest.approx(results['female'].expected, abs=1E-4)
    assert 0.0 == pytest.approx(results['female'].pvalue, abs=1E-4)
