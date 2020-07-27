"""
Created on Nov 7, 2016

@author: lubo
"""
from dae.gene.weights import GeneWeight


def test_weights_default(gene_info_config):
    config = gene_info_config.gene_weights.RVIS_rank
    w = GeneWeight("RVIS_rank", config)

    assert w.df is not None

    assert "RVIS_rank" in w.df.columns


def test_weights_min_max(gene_info_config):
    config = gene_info_config.gene_weights.LGD_rank
    w = GeneWeight("LGD_rank", config)

    assert 1.0 == w.min()
    assert 18394.5 == w.max()


def test_weights_get_genes(gene_info_config):
    config = gene_info_config.gene_weights.LGD_rank
    w = GeneWeight("LGD_rank", config)

    genes = w.get_genes(1.5, 5.0)
    assert 3 == len(genes)

    genes = w.get_genes(-1, 5.0)
    assert 4 == len(genes)

    genes = w.get_genes(1, 5.0)
    assert 4 == len(genes)
