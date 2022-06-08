# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import textwrap
import pytest

from dae.gene.gene_scores import GeneScoresDb, GeneScore
from dae.genomic_resources.testing import build_testing_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.fixture(scope="session")
def scores_repo():
    scores_repo = build_testing_repository(repo_id="scores", content={
        "RVIS_rank": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                gene_scores:
                  - id: RVIS_rank
                    filename: RVIS.csv
                    desc: RVIS rank
                histogram:
                  bins: 150
                  xscale: linear
                  yscale: linear
                """,
            "RVIS.csv": textwrap.dedent("""
                "gene","RVIS","RVIS_rank"
                "LRP1",-7.28,3
                "TRRAP",-6.14,6
                "ANKRD11",-4.38,15
                "ZFHX3",-4.26,19
                "HERC2",-5.99,8
                "TRIO",-4.04,29
                "MACF1",-3.92,34
                "PLEC",-6.57,5
                "SRRM2",-4.51,13
                "SPTBN1",-3.86,37
                "UBR4",-7.5,2
                "EP400",-3.86,36
                "NOTCH1",-3.51,55
                """)
        },
        "LGD_rank": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                gene_scores:
                  - id: LGD_rank
                    filename: LGD.csv
                    desc: LGD rank
                histogram:
                  bins: 150
                  xscale: linear
                  yscale: linear
                """,
            "LGD.csv": textwrap.dedent("""
                "gene","LGD_score","LGD_rank"
                "LRP1",0.000014,1
                "TRRAP",0.00016,3
                "ANKRD11",0.0004,5
                "ZFHX3",0.000925,8
                "HERC2",0.003682,25
                "TRIO",0.001563,11
                "MACF1",0.000442,6
                "PLEC",0.004842,40
                "SRRM2",0.004471,35
                "SPTBN1",0.002715,19.5
                "UBR4",0.007496,59
            """)
        }
    })
    return scores_repo


@pytest.fixture(scope="session")
def gene_scores_db(scores_repo):
    resources = [
        scores_repo.get_resource("LGD_rank"),
        scores_repo.get_resource("RVIS_rank"),
    ]
    scores = []
    for r in resources:
        scores += GeneScore.load_gene_scores_from_resource(r)
    return GeneScoresDb(scores)


def test_scores_rvis_rank(gene_scores_db):
    assert gene_scores_db["RVIS_rank"] is not None

    rvis = gene_scores_db["RVIS_rank"]
    assert rvis.df is not None

    assert "RVIS_rank" in rvis.df.columns


def test_scores_has_rvis_rank(gene_scores_db):
    assert "RVIS_rank" in gene_scores_db


def test_loaded_scores(gene_scores_db):
    assert len(gene_scores_db) == 2


def test_create_score_from_repository(scores_repo):
    resource = scores_repo.get_resource("RVIS_rank")
    score = GeneScore.load_gene_scores_from_resource(resource)
    assert score[0]
    print(score[0])


def test_scores_default(scores_repo):
    resource = scores_repo.get_resource("RVIS_rank")
    score = GeneScore.load_gene_scores_from_resource(resource)[0]
    assert score.df is not None

    assert "RVIS_rank" in score.df.columns


def test_scores_min_max(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = GeneScore.load_gene_scores_from_resource(resource)[0]

    assert 1.0 == score.min()
    assert 59.0 == score.max()


def test_scores_get_genes(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = GeneScore.load_gene_scores_from_resource(resource)[0]

    genes = score.get_genes(1.5, 5.1)
    assert len(genes) == 2

    genes = score.get_genes(-1, 5.1)
    assert len(genes) == 3

    genes = score.get_genes(1, 5.1)
    assert len(genes) == 3

    genes = score.get_genes(1, 5.0)
    assert len(genes) == 2


def test_scores_to_tsv(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = GeneScore.load_gene_scores_from_resource(resource)[0]
    tsv = list(score.to_tsv())

    assert len(tsv) == 12
    assert tsv[0] == "gene\tLGD_rank\n"
