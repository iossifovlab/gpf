'''
Created on Feb 28, 2018

@author: lubo
'''
from DAE import get_gene_sets_symNS


def test_gene_sets_sym():
    main_sets = get_gene_sets_symNS('main')
    assert main_sets is not None
    print(main_sets.t2G.keys())
    assert "autism candidates from Iossifov PNAS 2015" in main_sets.t2G
