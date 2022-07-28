# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pytest
import numpy as np

from dae.genomic_resources.testing import build_testing_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.gene.gene_scores import GeneScore


@pytest.fixture
def scores_repo(tmp_path):
    scores_repo = build_testing_repository(
        repo_id="scores",
        content={
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
                      min: 1
                      max: 4
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
            }
        },
        root_path=str(tmp_path)
    )

    return scores_repo


def test_load_linear_gene_scores_from_resource(scores_repo):

    res = scores_repo.get_resource("LinearHist")
    assert res.get_type() == "gene_score"

    result = GeneScore.load_gene_scores_from_resource(res)
    assert len(result) == 1

    gene_score = result[0]
    hist = gene_score.histogram
    assert len(hist.bins) == 4

    assert np.all(hist.bars == np.array([2, 2, 2]))


def test_load_log_gene_scores_from_resource(scores_repo):

    res = scores_repo.get_resource("LogHist")
    assert res.get_type() == "gene_score"

    result = GeneScore.load_gene_scores_from_resource(res)
    assert len(result) == 1

    gene_score = result[0]
    hist = gene_score.histogram
    assert len(hist.bins) == 6

    assert np.all(hist.bars == np.array([2, 1, 1, 1, 1]))
