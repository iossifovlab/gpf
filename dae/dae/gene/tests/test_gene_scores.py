"""
Created on Nov 7, 2016

@author: lubo
"""
from dae.gene.gene_scores import GeneScore


def test_create_score_from_repository(scores_repo):
    resource = scores_repo.get_resource("RVIS_rank")
    score = GeneScore.load_gene_score_from_resource(resource)
    assert score
    print(score)


def test_scores_default(scores_repo):
    resource = scores_repo.get_resource("RVIS_rank")
    w = GeneScore.load_gene_score_from_resource(resource)

    assert w.df is not None

    assert "RVIS_rank" in w.df.columns


def test_scores_min_max(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    w = GeneScore.load_gene_score_from_resource(resource)

    assert 1.0 == w.min()
    assert 18394.5 == w.max()


def test_scores_get_genes(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    w = GeneScore.load_gene_score_from_resource(resource)

    genes = w.get_genes(1.5, 5.0)
    assert 3 == len(genes)

    genes = w.get_genes(-1, 5.0)
    assert 4 == len(genes)

    genes = w.get_genes(1, 5.0)
    assert 4 == len(genes)


def test_scores_to_tsv(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = GeneScore.load_gene_score_from_resource(resource)
    tsv = list(score.to_tsv())
    assert len(tsv) == 18460
    assert tsv[0] == "gene\tLGD_rank\n"
