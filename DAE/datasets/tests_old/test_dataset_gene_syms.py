'''
Created on Feb 27, 2017

@author: lubo
'''
from __future__ import unicode_literals


def test_get_gene_syms_sd(sd):
    kwargs = {
        'geneSet': {
            'geneSetsCollection': 'denovo',
            'geneSet': 'LGDs.Recurrent',
            'geneSetsTypes': ['autism'],
        }
    }
    res = sd.get_gene_set_query(**kwargs)
