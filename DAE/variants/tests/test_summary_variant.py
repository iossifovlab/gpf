'''
Created on Jul 1, 2018

@author: lubo
'''
from variants.variant import SummaryAlleleDelegate


def test_summary_allele_delegate(sv):
    for sa in sv.alleles:
        sd = SummaryAlleleDelegate(sa)

        for attr in ['chromosome', 'position', 'reference', 'alternative',
                     'summary_index', 'allele_index', 'effect', 'frequency',
                     'details', 'is_reference_allele']:

            assert getattr(sa, attr) == getattr(sd, attr)
