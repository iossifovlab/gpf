# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
import pytest
import numpy as np

from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    GenomicResourceRepo
from dae.genomic_resources.histogram import NumberHistogram
from dae.gene.implementations.gene_scores_impl import \
    build_gene_score_from_resource, \
    GeneScoreImplementation


@pytest.fixture
def scores_repo(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    scores_repo = build_inmemory_test_repository({
        "LinearHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: linear.csv
                scores:
                - id: linear score
                  desc: linear gene score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "linear.csv": textwrap.dedent("""
                gene,linear score
                G1,1
                G2,2
                G3,3
                G4,1
                G5,2
                G6,3
            """),
            "statistics": {
                "histogram_linear score.yaml": textwrap.dedent("""
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
                      type: number
                      number_of_bins: 3
                      score: linear score
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
                  histogram:
                    type: number
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
                      type: number
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
        "NaNTest": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: scores.csv
                scores:
                - id: score1
                  desc: linear gene score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "scores.csv": textwrap.dedent("""
                gene,score1
                G1,1
                G2,2
                G3,nan
                G4,1
                G5,nan
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
                      type: number
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


def test_load_linear_gene_scores_from_resource(
        scores_repo: GenomicResourceRepo) -> None:

    res = scores_repo.get_resource("LinearHist")
    assert res.get_type() == "gene_score"

    result = build_gene_score_from_resource(res)
    scores = result.get_scores()
    assert len(scores) == 1
    score_id = scores[0]

    assert result.get_x_scale(score_id) == "linear"
    assert result.get_y_scale(score_id) == "linear"

    hist = result.get_score_histogram(score_id)
    assert hist is not None
    assert isinstance(hist, NumberHistogram)

    assert len(hist.bins) == 4

    assert np.all(hist.bars == np.array([2, 2, 2]))


def test_load_log_gene_scores_from_resource(
        scores_repo: GenomicResourceRepo) -> None:

    res = scores_repo.get_resource("LogHist")
    assert res.get_type() == "gene_score"

    result = build_gene_score_from_resource(res)
    scores = result.get_scores()
    assert len(scores) == 1
    score_id = scores[0]

    assert result.get_x_scale(score_id) == "log"
    assert result.get_y_scale(score_id) == "linear"

    hist = result.get_score_histogram(score_id)
    assert hist is not None
    assert isinstance(hist, NumberHistogram)

    assert len(hist.bins) == 6
    assert np.all(hist.bars == np.array([2, 1, 1, 1, 1]))


def test_load_wrong_resource_type(
        scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("Oops")
    with pytest.raises(ValueError, match="invalid resource type Oops"):
        build_gene_score_from_resource(res)


def test_load_gene_score_without_histogram(
        scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("OopsHist")
    with pytest.raises(
        ValueError,
        match="Missing histogram config for linear in OopsHist"
    ):
        build_gene_score_from_resource(res)


def test_load_gene_score_without_gene_scores(
        scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("OopsScores")
    with pytest.raises(ValueError,
                       match="missing scores config in OopsScores"):
        build_gene_score_from_resource(res)


def test_gene_score(scores_repo: GenomicResourceRepo) -> None:

    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    assert gene_score is not None

    assert gene_score.get_gene_value("linear score", "G2") == 2
    assert gene_score.get_gene_value("linear score", "G3") == 3


def test_gene_score_nan(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("NaNTest")
    gene_score = build_gene_score_from_resource(res)

    assert len(gene_score.df) == 6
    df = gene_score.get_score_df("score1")
    assert len(df) == 4


def test_calculate_histogram(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    result = build_gene_score_from_resource(res)
    assert result is not None

    histogram = GeneScoreImplementation._calc_histogram(res, "linear score")
    assert histogram is not None
    print(histogram.config.view_range[0])
    print(type(histogram.config.view_range[0]))
    print(histogram.serialize())


def test_get_histogram_image_url(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    result = build_gene_score_from_resource(res)
    assert result is not None

    histogram = result.get_score_histogram("linear score")
    assert histogram is not None

    url = result.get_histogram_image_url("linear score")
    assert url is not None

    assert url.endswith("histogram_linear%20score.png")
