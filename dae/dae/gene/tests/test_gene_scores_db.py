# pylint: disable=W0621,C0114,C0116,W0212,W0613,W0104

import textwrap
import pytest

from dae.gene.gene_scores import GeneScoresDb, GeneScore, \
    build_gene_score_from_resource
from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.fixture
def scores_repo(tmp_path):
    scores_repo = build_inmemory_test_repository({
        "RVIS_rank": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: RVIS.csv
                scores:
                  - id: RVIS_rank
                    desc: RVIS rank
                    number_hist:
                      number_of_bins: 150
                      x_log_scale: false
                      y_log_scale: false
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
                filename: LGD.csv
                scores:
                  - id: LGD_rank
                    desc: LGD rank
                    number_hist:
                     number_of_bins: 150
                     x_log_scale: false
                     y_log_scale: false
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


@pytest.fixture
def gene_scores_db(scores_repo):
    resources = [
        scores_repo.get_resource("LGD_rank"),
        scores_repo.get_resource("RVIS_rank"),
    ]
    gene_scores = []
    for resource in resources:
        gene_scores.append(build_gene_score_from_resource(resource))
    return GeneScoresDb(gene_scores)


def test_scores_rvis_rank(gene_scores_db):
    assert gene_scores_db["RVIS_rank"] is not None

    rvis = gene_scores_db.get_gene_score("RVIS_rank")
    assert rvis.df is not None

    assert "RVIS_rank" in rvis.df.columns


def test_scores_has_rvis_rank(gene_scores_db):
    assert "RVIS_rank" in gene_scores_db


def test_missing_gene_score(gene_scores_db):
    with pytest.raises(ValueError, match="score bad_score not found"):
        gene_scores_db["bad_score"]


def test_loaded_scores(gene_scores_db):
    assert len(gene_scores_db) == 2


def test_gene_scores_ids(gene_scores_db):
    assert gene_scores_db.get_gene_score_ids() == ["LGD_rank", "RVIS_rank"]


def test_gene_scores(gene_scores_db):
    gene_scores = gene_scores_db.get_scores()
    assert sorted(gs.score_id for gs in gene_scores) == \
        ["LGD_rank", "RVIS_rank"]


def test_create_score_from_repository(scores_repo):
    resource = scores_repo.get_resource("RVIS_rank")
    score = build_gene_score_from_resource(resource)
    assert score
    print(score)


def test_scores_default(scores_repo):
    resource = scores_repo.get_resource("RVIS_rank")
    score = build_gene_score_from_resource(resource)
    assert score.df is not None

    assert "RVIS_rank" in score.df.columns


def test_scores_min_max(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = build_gene_score_from_resource(resource)

    assert score.get_min("LGD_rank") == 1.0
    assert score.get_max("LGD_rank") == 59.0


def test_scores_get_genes(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = build_gene_score_from_resource(resource)

    genes = score.get_genes("LGD_rank", 1.5, 5.1)
    assert len(genes) == 2

    genes = score.get_genes("LGD_rank", -1, 5.1)
    assert len(genes) == 3

    genes = score.get_genes("LGD_rank", 1, 5.1)
    assert len(genes) == 3

    genes = score.get_genes("LGD_rank", 1, 5.0)
    assert len(genes) == 2


def test_scores_to_tsv(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = build_gene_score_from_resource(resource)
    tsv = list(score.to_tsv("LGD_rank"))

    assert len(tsv) == 12
    assert tsv[0] == "gene\tLGD_rank\n"
