"""
Created on Nov 7, 2016

@author: lubo
"""
from dae.gene.weights import GeneWeight


def test_create_weight_from_repository(weights_repo):
    resource = weights_repo.get_resource("RVIS_rank")
    weight = GeneWeight.load_gene_weight_from_resource(resource)
    assert weight
    print(weight)


def test_weights_default(weights_repo):
    resource = weights_repo.get_resource("RVIS_rank")
    w = GeneWeight.load_gene_weight_from_resource(resource)

    assert w.df is not None

    assert "RVIS_rank" in w.df.columns


def test_weights_min_max(weights_repo):
    resource = weights_repo.get_resource("LGD_rank")
    w = GeneWeight.load_gene_weight_from_resource(resource)

    assert 1.0 == w.min()
    assert 18394.5 == w.max()


def test_weights_get_genes(weights_repo):
    resource = weights_repo.get_resource("LGD_rank")
    w = GeneWeight.load_gene_weight_from_resource(resource)

    genes = w.get_genes(1.5, 5.0)
    assert 3 == len(genes)

    genes = w.get_genes(-1, 5.0)
    assert 4 == len(genes)

    genes = w.get_genes(1, 5.0)
    assert 4 == len(genes)


def test_weights_to_tsv(weights_repo):
    resource = weights_repo.get_resource("LGD_rank")
    weight = GeneWeight.load_gene_weight_from_resource(resource)
    tsv = list(weight.to_tsv())
    assert len(tsv) == 18460
    assert tsv[0] == "gene\tLGD_rank\n"
