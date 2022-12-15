# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pytest
import numpy as np

from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.gene.gene_scores import GeneScore


@pytest.fixture
def scores_repo(tmp_path):
    scores_repo = build_inmemory_test_repository({
        "LinearHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: linear.csv
                gene_scores:
                - id: linear
                  desc: linear gene score
                histograms:
                - score: linear
                  bins: 3
                  x_scale: linear
                  y_scale: linear
                """,
            "linear.csv": textwrap.dedent("""
                gene,linear
                G1,1
                G2,2
                G3,3
                G4,1
                G5,2
                G6,3
            """)
        },
        "LogHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: log.csv
                gene_scores:
                - id: log
                  desc: log gene score
                histograms:
                - score: log
                  bins: 5
                  min: 0.0
                  max: 1.0
                  x_min_log: 0.001
                  x_scale: log
                  y_scale: linear
                """,
            "log.csv": textwrap.dedent("""
                gene,log
                G1,0
                G2,0.0001
                G3,0.001
                G4,0.01
                G5,0.1
                G6,1.0
            """)
        },
        "Oops": {
            GR_CONF_FILE_NAME: "",
        },
        "OopsHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: oops.csv
                gene_scores:
                - id: linear
                  desc: linear gene score
                """,
            "oops.csv": textwrap.dedent("""
                gene,linear
                G1,1
                G2,2
                G3,3
            """)
        },
        "OopsScores": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: oops.csv
                """,
            "oops.csv": textwrap.dedent("""
                gene,linear
                G1,1
                G2,2
                G3,3
            """)
        },
        "OopsMissingHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: linear.csv
                gene_scores:
                - id: linear
                  desc: linear gene score
                histograms:
                - score: alabala
                  bins: 3
                  x_scale: linear
                  y_scale: linear
                """,
            "linear.csv": textwrap.dedent("""
                gene,alabala
                G1,1
                G2,2
                G3,3
            """)
        },
    })
    return scores_repo


def test_load_linear_gene_scores_from_resource(scores_repo):

    res = scores_repo.get_resource("LinearHist")
    assert res.get_type() == "gene_score"

    result = GeneScore.load_gene_scores_from_resource(res)
    assert len(result) == 1

    gene_score = result[0]
    assert gene_score.x_scale == "linear"
    assert gene_score.y_scale == "linear"

    hist = gene_score.histogram
    assert len(hist.bins) == 4

    assert np.all(hist.bars == np.array([2, 2, 2]))


def test_load_log_gene_scores_from_resource(scores_repo):

    res = scores_repo.get_resource("LogHist")
    assert res.get_type() == "gene_score"

    result = GeneScore.load_gene_scores_from_resource(res)
    assert len(result) == 1

    gene_score = result[0]
    assert gene_score.x_scale == "log"
    assert gene_score.y_scale == "linear"

    hist = gene_score.histogram
    assert len(hist.bins) == 6

    assert np.all(hist.bars == np.array([2, 1, 1, 1, 1]))


def test_load_wrong_resource_type(scores_repo):
    res = scores_repo.get_resource("Oops")
    with pytest.raises(ValueError, match="invalid resource type Oops"):
        GeneScore.load_gene_scores_from_resource(res)


def test_load_gene_score_without_histogram(scores_repo):
    res = scores_repo.get_resource("OopsHist")
    with pytest.raises(ValueError, match="missing histograms config OopsHist"):
        GeneScore.load_gene_scores_from_resource(res)


def test_load_gene_score_without_gene_scores(scores_repo):
    res = scores_repo.get_resource("OopsScores")
    with pytest.raises(ValueError,
                       match="missing gene_scores config OopsScores"):
        GeneScore.load_gene_scores_from_resource(res)


def test_load_gene_score_with_missing_score_hist(scores_repo):
    res = scores_repo.get_resource("OopsMissingHist")
    with pytest.raises(ValueError,
                       match="missing histogram config for score linear in "
                       "resource OopsMissingHist"):
        GeneScore.load_gene_scores_from_resource(res)


def test_gene_score(scores_repo):

    res = scores_repo.get_resource("LinearHist")
    result = GeneScore.load_gene_scores_from_resource(res)
    assert len(result) == 1

    gene_score = result[0]

    assert gene_score.get_gene_value("G2") == 2
    assert gene_score.get_gene_value("G3") == 3
