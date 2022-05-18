import pytest

from dae.gene.gene_scores import GeneScoresDb, GeneScore
from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.fixture(scope="session")
def scores_repo():
    scores_repo = GenomicResourceEmbededRepo("scores", content={
        "RVIS_rank": {
            GR_CONF_FILE_NAME: (
                "type: gene_score\n"
                "gene_scores:\n"
                "  - id: RVIS_rank\n"
                "    filename: RVIS.csv\n"
                "    desc: RVIS rank\n"
                "histograms:\n"
                "  - score: RVIS_rank\n"
                "    bins: 150\n"
                "    xscale: linear\n"
                "    yscale: linear\n"
            ),
            "RVIS.csv": (
                "\"gene\",\"RVIS\",\"RVIS_rank\"\n"
                "\"LRP1\",-7.28,3\n"
                "\"TRRAP\",-6.14,6\n"
                "\"ANKRD11\",-4.38,15\n"
                "\"ZFHX3\",-4.26,19\n"
                "\"HERC2\",-5.99,8\n"
                "\"TRIO\",-4.04,29\n"
                "\"MACF1\",-3.92,34\n"
                "\"PLEC\",-6.57,5\n"
                "\"SRRM2\",-4.51,13\n"
                "\"SPTBN1\",-3.86,37\n"
                "\"UBR4\",-7.5,2\n"
                "\"EP400\",-3.86,36\n"
                "\"NOTCH1\",-3.51,55\n"
            )
        },
        "LGD_rank": {
            GR_CONF_FILE_NAME: (
                "type: gene_score\n"
                "gene_scores:\n"
                "  - id: LGD_rank\n"
                "    filename: LGD.csv\n"
                "    desc: LGD rank\n"
                "histograms:\n"
                "  - score: LGD_rank\n"
                "    bins: 150\n"
                "    xscale: linear\n"
                "    yscale: linear\n"
            ),
            "LGD.csv": (
                "\"gene\",\"LGD_score\",\"LGD_rank\"\n"
                "\"LRP1\",0.000014,1\n"
                "\"TRRAP\",0.00016,3\n"
                "\"ANKRD11\",0.0004,5\n"
                "\"ZFHX3\",0.000925,8\n"
                "\"HERC2\",0.003682,25\n"
                "\"TRIO\",0.001563,11\n"
                "\"MACF1\",0.000442,6\n"
                "\"PLEC\",0.004842,40\n"
                "\"SRRM2\",0.004471,35\n"
                "\"SPTBN1\",0.002715,19.5\n"
                "\"UBR4\",0.007496,59\n"
            )
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
    w = GeneScore.load_gene_scores_from_resource(resource)[0]

    assert w.df is not None

    assert "RVIS_rank" in w.df.columns


def test_scores_min_max(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    w = GeneScore.load_gene_scores_from_resource(resource)[0]

    assert 1.0 == w.min()
    assert 59.0 == w.max()


def test_scores_get_genes(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    w = GeneScore.load_gene_scores_from_resource(resource)[0]

    genes = w.get_genes(1.5, 5.1)
    assert len(genes) == 2

    genes = w.get_genes(-1, 5.1)
    assert len(genes) == 3

    genes = w.get_genes(1, 5.1)
    assert len(genes) == 3

    genes = w.get_genes(1, 5.0)
    assert len(genes) == 2


def test_scores_to_tsv(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    score = GeneScore.load_gene_scores_from_resource(resource)[0]
    tsv = list(score.to_tsv())
    assert len(tsv) == 12
    assert tsv[0] == "gene\tLGD_rank\n"
