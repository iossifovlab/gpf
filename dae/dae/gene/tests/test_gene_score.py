# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pytest
import numpy as np

from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.gene.gene_scores import build_gene_score_from_resource, \
    GeneScoreImplementation


@pytest.fixture
def scores_repo(tmp_path):
    scores_repo = build_inmemory_test_repository({
        "LinearHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: linear.csv
                scores:
                - id: linear
                  desc: linear gene score
                  number_hist:
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "linear.csv": textwrap.dedent("""
                gene,linear
                G1,1
                G2,2
                G3,3
                G4,1
                G5,2
                G6,3
            """),
            "statistics": {
                "histogram_linear.yaml": textwrap.dedent("""
                    bars:
                    - 2
                    - 2
                    - 2
                    bins:
                    - 1.0
                    - 1.665
                    - 2.333
                    - 3.0
                    config:
                      number_of_bins: 3
                      score: linear
                      view_range:
                        max: 3.0
                        min: 1.0
                      x_log_scale: false
                      y_log_scale: false
                """)
            }
        },
        "LogHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: log.csv
                scores:
                - id: log
                  desc: log gene score
                  number_hist:
                    number_of_bins: 5
                    view_range:
                      min: 0.0
                      max: 1.0
                    x_min_log: 0.001
                    x_log_scale: true
                    y_log_scale: false
                """,
            "log.csv": textwrap.dedent("""
                gene,log
                G1,0
                G2,0.0001
                G3,0.001
                G4,0.01
                G5,0.1
                G6,1.0
            """),
            "statistics": {
                "histogram_log.yaml": textwrap.dedent("""
                    bars:
                    - 2
                    - 1
                    - 1
                    - 1
                    - 1
                    bins:
                    - 0.0,
                    - 0.001,
                    - 0.005623413251903491,
                    - 0.03162277660168379,
                    - 0.1778279410038923,
                    - 1.0
                    config:
                      desc: log gene score
                      number_hist:
                      number_of_bins: 5
                      view_range:
                        min: 0.0
                        max: 1.0
                      x_min_log: 0.001
                      x_log_scale: true
                      y_log_scale: false
                """)
            }
        },
        "Oops": {
            GR_CONF_FILE_NAME: "",
        },
        "OopsHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: oops.csv
                scores:
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
    })
    return scores_repo


def test_load_linear_gene_scores_from_resource(scores_repo):

    res = scores_repo.get_resource("LinearHist")
    assert res.get_type() == "gene_score"

    result = build_gene_score_from_resource(res)
    scores = result.get_scores()
    assert len(scores) == 1
    score_id = scores[0]

    assert result.get_x_scale(score_id) == "linear"
    assert result.get_y_scale(score_id) == "linear"

    hist = result.get_histogram(score_id)
    assert len(hist.bins) == 4

    assert np.all(hist.bars == np.array([2, 2, 2]))


def test_load_log_gene_scores_from_resource(scores_repo):

    res = scores_repo.get_resource("LogHist")
    assert res.get_type() == "gene_score"

    result = build_gene_score_from_resource(res)
    scores = result.get_scores()
    assert len(scores) == 1
    score_id = scores[0]

    assert result.get_x_scale(score_id) == "log"
    assert result.get_y_scale(score_id) == "linear"

    hist = result.get_histogram(score_id)
    assert len(hist.bins) == 6

    assert np.all(hist.bars == np.array([2, 1, 1, 1, 1]))


def test_load_wrong_resource_type(scores_repo):
    res = scores_repo.get_resource("Oops")
    with pytest.raises(ValueError, match="invalid resource type Oops"):
        build_gene_score_from_resource(res)


def test_load_gene_score_without_histogram(scores_repo):
    res = scores_repo.get_resource("OopsHist")
    with pytest.raises(
        ValueError,
        match="Missing histogram config for linear in OopsHist"
    ):
        build_gene_score_from_resource(res)


def test_load_gene_score_without_gene_scores(scores_repo):
    res = scores_repo.get_resource("OopsScores")
    with pytest.raises(ValueError,
                       match="missing scores config in OopsScores"):
        build_gene_score_from_resource(res)


def test_gene_score(scores_repo):

    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    assert gene_score is not None

    assert gene_score.get_gene_value("linear", "G2") == 2
    assert gene_score.get_gene_value("linear", "G3") == 3


def test_calculate_histogram(scores_repo):
    res = scores_repo.get_resource("LinearHist")
    result = build_gene_score_from_resource(res)
    assert result is not None

    histogram = GeneScoreImplementation._calc_histogram(res, "linear")
    assert histogram is not None
    print(histogram.config.view_range[0])
    print(type(histogram.config.view_range[0]))
    print(histogram.serialize())
