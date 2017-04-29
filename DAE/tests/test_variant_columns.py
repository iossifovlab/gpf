'''
Created on Sep 27, 2016

@author: lubo
'''
from query_variants import do_query_variants, dae_query_variants, augment_vars
import itertools


def test_dae_query():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
    }

    vs = dae_query_variants(query)

    for v in itertools.chain(*vs):
        assert v


def test_do_query():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
    }

    vs = do_query_variants(query)

    for v in vs:
        assert v


def test_variant_phenotype_augment_attribute():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
    }

    vs = dae_query_variants(query)

    for v in itertools.chain(*vs):
        v = augment_vars(v)
        assert '_phenotype_' in v.atts
        assert 'autism' == v.atts['_phenotype_']
        assert 'autism' == getattr(v, '_phenotype_')
