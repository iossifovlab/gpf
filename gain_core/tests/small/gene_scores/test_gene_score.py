# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import logging
import textwrap

import numpy as np
import pytest
from gain.gene_scores.gene_scores import (
    GeneScore,
    GeneScoresDb,
    ScoreDesc,
    _build_gene_score_help,
    build_gene_score_from_resource,
    build_gene_score_from_resource_id,
)
from gain.gene_scores.implementations.gene_scores_impl import (
    GeneScoreImplementation,
)
from gain.genomic_resources.histogram import (
    CategoricalHistogram,
    NumberHistogram,
)
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from gain.genomic_resources.testing import build_inmemory_test_repository
from gain.task_graph.graph import TaskDesc


@pytest.fixture
def scores_repo() -> GenomicResourceRepo:
    return build_inmemory_test_repository({
        "LinearHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: linear.csv
                scores:
                - id: linear score
                  type: float
                  column_name: linear_score
                  desc: linear gene score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "linear.csv": textwrap.dedent("""
                gene,linear_score
                G1,1
                G2,2
                G3,3
                G4,1
                G5,2
                G6,3
            """),
            "statistics": {
                "histogram_linear score.json": textwrap.dedent("""{
                    "bars":[2,2,2],
                    "bins":[1.0,1.665,2.333,3.0],
                    "config":{
                      "type": "number",
                      "number_of_bins": 3,
                      "score": "linear score",
                      "view_range": {
                        "max": 3.0,
                        "min": 1.0
                      },
                      "x_log_scale": false,
                      "y_log_scale": false
                    }
                }
                """),
            },
        },
        "LinearHistInt": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: linear.csv
                scores:
                - id: int score
                  type: int
                  column_name: int_score
                  desc: test int score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "linear.csv": textwrap.dedent("""
                gene,int_score
                G1,1
                G2,2
                G3,3
                G4,1
                G5,2
                G6,3
            """),
            "statistics": {
                "histogram_linear score.json": textwrap.dedent("""{
                    "bars":[2,2,2],
                    "bins":[1.0,1.665,2.333,3.0],
                    "config":{
                      "type": "number",
                      "number_of_bins": 3,
                      "score": "linear score",
                      "view_range": {
                        "max": 3.0,
                        "min": 1.0
                      },
                      "x_log_scale": false,
                      "y_log_scale": false
                    }
                }
                """),
            },
        },
        "LogHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: log.csv
                scores:
                - id: log
                  type: float
                  column_name: log_score
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
                gene,log_score
                G1,0
                G2,0.0001
                G3,0.001
                G4,0.01
                G5,0.1
                G6,1.0
            """),
            "statistics": {
                "histogram_log.json": textwrap.dedent("""{
                    "bars":[2,1,1,1,1],
                    "bins": [
                        0.0,0.001,0.005623413251903491,0.03162277660168379,
                        0.1778279410038923,1.0],
                    "config": {
                        "type": "number",
                        "number_of_bins": 5,
                        "view_range": {
                            "min": 0.0,
                            "max": 1.0
                        },
                        "x_min_log": 0.001,
                        "x_log_scale": true,
                        "y_log_scale": false
                    }
                }
                """),
            },
        },
        "LogHistENotation": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: log.csv
                scores:
                - id: log
                  type: float
                  column_name: log_score
                  desc: log gene score
                  histogram:
                    type: number
                    number_of_bins: 5
                    view_range:
                      min: 0.0
                      max: 1.0
                    x_min_log: 1.0e-3
                    x_log_scale: true
                    y_log_scale: false
                """,
            "log.csv": textwrap.dedent("""
                gene,log_score
                G1,0
                G2,0.0001
                G3,0.001
                G4,0.01
                G5,0.1
                G6,1.0
            """),
            "statistics": {
                "histogram_log.json": textwrap.dedent("""{
                    "bars":[2,1,1,1,1],
                    "bins": [
                        0.0,0.001,0.005623413251903491,0.03162277660168379,
                        0.1778279410038923,1.0],
                    "config": {
                        "type": "number",
                        "number_of_bins": 5,
                        "view_range": {
                            "min": 0.0,
                            "max": 1.0
                        },
                        "x_min_log": 1.0e-3,
                        "x_log_scale": true,
                        "y_log_scale": false
                    }
                }
                """),
            },
        },
        "NaNTest": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: scores.csv
                scores:
                - id: score1
                  column_name: score_1
                  desc: linear gene score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "scores.csv": textwrap.dedent("""
                gene,score_1
                G1,1
                G2,2
                G3,nan
                G4,1
                G5,nan
                G6,3
            """),
            "statistics": {
                "histogram_linear.json": textwrap.dedent("""{
                    "bars":[
                        2,
                        2,
                        2
                    ],
                    "bins": [
                        1.0,
                        1.665,
                        2.333,
                        3.0
                    ],
                    "config": {
                      "type": "number",
                      "number_of_bins": 3,
                      "score": "linear",
                      "view_range": {
                        max: 3.0,
                        min: 1.0
                      }
                      "x_log_scale": false,
                      "y_log_scale": false
                    }
                }
                """),
            },
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
                  type: int
                  desc: linear gene score
                """,
            "oops.csv": textwrap.dedent("""
                gene,linear
                G1,1
                G2,2
                G3,3
            """),
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
            """),
        },
    })


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


def test_load_log_gene_scores_from_resource_with_e_notation(
        scores_repo: GenomicResourceRepo) -> None:

    res = scores_repo.get_resource("LogHistENotation")
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
    with pytest.raises(ValueError, match="invalid resource type: Oops"):
        build_gene_score_from_resource(res)


def test_load_gene_score_without_histogram(
        scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("OopsHist")
    with pytest.raises(
        TypeError,
        match="Missing histogram config for linear in OopsHist",
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


def test_gene_score_get_genes(scores_repo: GenomicResourceRepo) -> None:

    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    assert gene_score is not None

    assert gene_score.get_genes(
        "linear score", score_min=2, score_max=3) == {"G2", "G3", "G5", "G6"}


def test_gene_score_nan(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("NaNTest")
    gene_score = build_gene_score_from_resource(res)

    assert len(gene_score.df) == 6
    df = gene_score.get_score_df("score1")
    assert len(df) == 4

    assert gene_score.get_gene_value("score1", "G3") is None


def test_calculate_histogram(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    result = build_gene_score_from_resource(res)
    assert result is not None

    histogram = GeneScoreImplementation._calc_histogram(result, "linear score")
    assert histogram is not None


def test_get_histogram_image_url(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    result = build_gene_score_from_resource(res)
    assert result is not None

    histogram = result.get_score_histogram("linear score")
    assert histogram is not None

    url = result.get_histogram_image_url("linear score")
    assert url is not None
    assert url.endswith("histogram_linear%20score.png")


def test_build_gene_scores_from_resource_id(
    scores_repo: GenomicResourceRepo,
) -> None:
    gs = build_gene_score_from_resource_id("LinearHist", scores_repo)
    assert gs is not None
    assert len(gs.get_scores()) == 1


def test_build_gene_score_help(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)
    assert gene_score is not None

    # Get the score definition
    score_def = gene_score.score_definitions["linear score"]
    assert score_def is not None

    # Build the help text
    help_text = _build_gene_score_help(score_def, gene_score)

    # Verify the help text contains expected elements
    assert help_text is not None
    assert len(help_text) > 0
    assert "linear score" in help_text
    assert "linear gene score" in help_text
    assert "LinearHist" in help_text
    assert '<div class="score-description">' in help_text
    assert "Genomic resource:" in help_text
    assert "histogram" in help_text.lower()


def test_gene_scores_db_initialization(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb initialization with gene scores."""
    res1 = scores_repo.get_resource("LinearHist")
    gene_score1 = build_gene_score_from_resource(res1)

    res2 = scores_repo.get_resource("LogHist")
    gene_score2 = build_gene_score_from_resource(res2)

    db = GeneScoresDb([gene_score1, gene_score2])

    assert db is not None
    assert len(db.get_gene_score_ids()) == 2
    assert "LinearHist" in db.get_gene_score_ids()
    assert "LogHist" in db.get_gene_score_ids()


def test_gene_scores_db_get_score_ids(scores_repo: GenomicResourceRepo) -> None:
    """Test GeneScoresDb.get_score_ids method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    score_ids = db.get_score_ids()
    assert len(score_ids) == 1
    assert "linear score" in score_ids


def test_gene_scores_db_get_gene_scores(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb.get_gene_scores method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    gene_scores = db.get_gene_scores()
    assert len(gene_scores) == 1
    assert gene_scores[0] == gene_score


def test_gene_scores_db_get_scores(scores_repo: GenomicResourceRepo) -> None:
    """Test GeneScoresDb.get_scores method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    scores = db.get_scores()
    assert len(scores) == 1
    assert isinstance(scores[0], ScoreDesc)
    assert scores[0].score_id == "linear score"


def test_gene_scores_db_get_gene_score(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb.get_gene_score method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    retrieved = db.get_gene_score("LinearHist")
    assert retrieved is not None
    assert retrieved == gene_score


def test_gene_scores_db_get_gene_score_missing(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb.get_gene_score with missing score."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    retrieved = db.get_gene_score("NonExistent")
    assert retrieved is None


def test_gene_scores_db_get_score_desc(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb.get_score_desc method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    score_desc = db.get_score_desc("linear score")
    assert score_desc is not None
    assert isinstance(score_desc, ScoreDesc)
    assert score_desc.score_id == "linear score"


def test_gene_scores_db_get_score_desc_missing(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb.get_score_desc with missing score."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    score_desc = db.get_score_desc("nonexistent")
    assert score_desc is None


def test_gene_scores_db_getitem(scores_repo: GenomicResourceRepo) -> None:
    """Test GeneScoresDb __getitem__ method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    score_desc = db["linear score"]
    assert score_desc is not None
    assert isinstance(score_desc, ScoreDesc)
    assert score_desc.score_id == "linear score"


def test_gene_scores_db_getitem_missing(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb __getitem__ with missing score raises error."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    with pytest.raises(ValueError, match=r"score .* not found"):
        _ = db["nonexistent"]


def test_gene_scores_db_contains(scores_repo: GenomicResourceRepo) -> None:
    """Test GeneScoresDb __contains__ method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    assert "linear score" in db
    assert "nonexistent" not in db


def test_gene_scores_db_len(scores_repo: GenomicResourceRepo) -> None:
    """Test GeneScoresDb __len__ method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    assert len(db) == 1


def test_gene_scores_db_empty() -> None:
    """Test GeneScoresDb with no gene scores."""
    db = GeneScoresDb([])

    assert len(db) == 0
    assert len(db.get_score_ids()) == 0
    assert len(db.get_gene_score_ids()) == 0
    assert len(db.get_scores()) == 0
    assert "anything" not in db


def test_gene_scores_db_build_descs_from_score(
    scores_repo: GenomicResourceRepo,
) -> None:
    """Test GeneScoresDb.build_descs_from_score method."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    score_descs = GeneScoresDb.build_descs_from_score(gene_score)

    assert len(score_descs) == 1
    assert isinstance(score_descs[0], ScoreDesc)
    assert score_descs[0].score_id == "linear score"
    assert score_descs[0].resource_id == "LinearHist"
    assert score_descs[0].column_name == "linear_score"
    assert score_descs[0].description == "linear gene score"
    assert isinstance(score_descs[0].hist, NumberHistogram)
    assert score_descs[0].help is not None


def test_gene_scores_db_multiple_scores_per_resource() -> None:
    """Test GeneScoresDb with resource containing multiple scores."""
    # Create a resource with multiple scores
    multi_score_repo = build_inmemory_test_repository({
        "MultiScore": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: multi.csv
                scores:
                - id: score1
                  desc: first score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                - id: score2
                  desc: second score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "multi.csv": textwrap.dedent("""
                gene,score1,score2
                G1,1,10
                G2,2,20
                G3,3,30
            """),
            "statistics": {
                "histogram_score1.json": textwrap.dedent("""{
                    "bars":[1,1,1],
                    "bins":[1.0,1.665,2.333,3.0],
                    "config":{
                      "type": "number",
                      "number_of_bins": 3,
                      "view_range": {"max": 3.0, "min": 1.0},
                      "x_log_scale": false,
                      "y_log_scale": false
                    }
                }"""),
                "histogram_score2.json": textwrap.dedent("""{
                    "bars":[1,1,1],
                    "bins":[10.0,16.65,23.33,30.0],
                    "config":{
                      "type": "number",
                      "number_of_bins": 3,
                      "view_range": {"max": 30.0, "min": 10.0},
                      "x_log_scale": false,
                      "y_log_scale": false
                    }
                }"""),
            },
        },
    })

    res = multi_score_repo.get_resource("MultiScore")
    gene_score = build_gene_score_from_resource(res)

    db = GeneScoresDb([gene_score])

    assert len(db) == 2
    assert "score1" in db
    assert "score2" in db
    assert len(db.get_gene_score_ids()) == 1
    assert "MultiScore" in db.get_gene_score_ids()


def test_score_desc_properties(scores_repo: GenomicResourceRepo) -> None:
    """Test ScoreDesc dataclass properties."""
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    score_descs = GeneScoresDb.build_descs_from_score(gene_score)
    score_desc = score_descs[0]

    assert score_desc.resource_id == "LinearHist"
    assert score_desc.score_id == "linear score"
    assert score_desc.column_name == "linear_score"
    assert isinstance(score_desc.hist, NumberHistogram)
    assert score_desc.description == "linear gene score"
    assert score_desc.help is not None
    assert len(score_desc.help) > 0
    assert score_desc.small_values_desc is None
    assert score_desc.large_values_desc is None


# ---------------------------------------------------------------------------
# get_genes with values= (categorical isin branch)
# ---------------------------------------------------------------------------

def test_get_genes_with_values(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    # Genes with score value 1: G1, G4.  Genes with score value 3: G3, G6.
    genes = gene_score.get_genes("linear score", values=["1", "3"])
    assert genes == {"G1", "G4", "G3", "G6"}


def test_get_genes_with_values_no_match(
    scores_repo: GenomicResourceRepo,
) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    genes = gene_score.get_genes("linear score", values=["99"])
    assert genes == set()


# ---------------------------------------------------------------------------
# get_gene_value - score_id not in gene_values entry
# ---------------------------------------------------------------------------

def test_get_gene_value_unknown_score_id(
    scores_repo: GenomicResourceRepo,
) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    # Manually remove the score from one gene's entry to exercise the
    # "score_id not in self.gene_values[gene_symbol]" branch.
    del gene_score.gene_values["G1"]["linear score"]
    assert gene_score.get_gene_value("linear score", "G1") is None


# ---------------------------------------------------------------------------
# get_values
# ---------------------------------------------------------------------------

def test_get_values(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    values = gene_score.get_values("linear score")
    assert isinstance(values, list)
    assert len(values) == 6
    assert sorted(values) == [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]


# ---------------------------------------------------------------------------
# get_score_range
# ---------------------------------------------------------------------------

def test_get_score_range_numeric() -> None:
    # Use a histogram JSON that includes min_value / max_value so that
    # get_score_range returns a meaningful (non-nan) tuple.
    range_repo = build_inmemory_test_repository({
        "RangeScore": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: scores.csv
                scores:
                - id: score1
                  desc: a score
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
                G3,3
            """),
            "statistics": {
                "histogram_score1.json": json.dumps({
                    "bars": [1, 1, 1],
                    "bins": [1.0, 1.665, 2.333, 3.0],
                    "min_value": 1.0,
                    "max_value": 3.0,
                    "config": {
                        "type": "number",
                        "number_of_bins": 3,
                        "view_range": {"min": 1.0, "max": 3.0},
                        "x_log_scale": False,
                        "y_log_scale": False,
                    },
                }),
            },
        },
    })
    res = range_repo.get_resource("RangeScore")
    gene_score = build_gene_score_from_resource(res)

    result = gene_score.get_score_range("score1")
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == 1.0
    assert result[1] == 3.0


def test_get_score_range_unknown_score(
    scores_repo: GenomicResourceRepo,
) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    with pytest.raises(ValueError, match="unknown score nonexistent"):
        gene_score.get_score_range("nonexistent")


def test_get_score_range_categorical() -> None:
    cat_repo = build_inmemory_test_repository({
        "CatScore": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: cat.csv
                scores:
                - id: cat
                  desc: categorical score
                  histogram:
                    type: categorical
                    value_order: [1, 2, 3]
                """,
            "cat.csv": textwrap.dedent("""
                gene,cat
                G1,1
                G2,2
                G3,3
            """),
            "statistics": {
                "histogram_cat.json": json.dumps({
                    "config": {
                        "type": "categorical",
                        "value_order": [1, 2, 3],
                        "y_log_scale": False,
                        "label_rotation": 0,
                    },
                    "values": {"1": 1, "2": 1, "3": 1},
                }),
            },
        },
    })
    res = cat_repo.get_resource("CatScore")
    gene_score = build_gene_score_from_resource(res)

    assert gene_score.get_score_range("cat") is None


# ---------------------------------------------------------------------------
# get_score_histogram - unknown score_id
# ---------------------------------------------------------------------------

def test_get_score_histogram_unknown_score(
    scores_repo: GenomicResourceRepo,
) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    with pytest.raises(ValueError, match="unknown score nonexistent"):
        gene_score.get_score_histogram("nonexistent")


# ---------------------------------------------------------------------------
# get_x_scale / get_y_scale - categorical and unknown score_id
# ---------------------------------------------------------------------------

@pytest.fixture
def cat_gene_score() -> GeneScore:
    cat_repo = build_inmemory_test_repository({
        "CatScore": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: cat.csv
                scores:
                - id: cat
                  desc: categorical score
                  histogram:
                    type: categorical
                    value_order: [1, 2, 3]
                """,
            "cat.csv": textwrap.dedent("""
                gene,cat
                G1,1
                G2,2
                G3,3
            """),
            "statistics": {
                "histogram_cat.json": json.dumps({
                    "config": {
                        "type": "categorical",
                        "value_order": [1, 2, 3],
                        "y_log_scale": False,
                        "label_rotation": 0,
                    },
                    "values": {"1": 1, "2": 1, "3": 1},
                }),
            },
        },
    })
    res = cat_repo.get_resource("CatScore")
    return build_gene_score_from_resource(res)


def test_get_x_scale_categorical(cat_gene_score: GeneScore) -> None:
    assert cat_gene_score.get_x_scale("cat") is None


def test_get_y_scale_categorical(cat_gene_score: GeneScore) -> None:
    assert cat_gene_score.get_y_scale("cat") is None


def test_get_x_scale_unknown_score(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    with pytest.raises(ValueError, match="unexpected score_id"):
        gene_score.get_x_scale("nonexistent")


def test_get_y_scale_unknown_score(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    gene_score = build_gene_score_from_resource(res)

    with pytest.raises(ValueError, match="unexpected score_id"):
        gene_score.get_y_scale("nonexistent")


# ---------------------------------------------------------------------------
# get_histogram_filename - YAML path
# ---------------------------------------------------------------------------

def test_get_histogram_filename_yaml() -> None:
    yaml_repo = build_inmemory_test_repository({
        "YamlHist": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: scores.csv
                scores:
                - id: score1
                  desc: a score
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
                G3,3
            """),
            "statistics": {
                "histogram_score1.yaml": textwrap.dedent("""
                    bars: [1, 1, 1]
                    bins: [1.0, 1.665, 2.333, 3.0]
                    config:
                      type: number
                      number_of_bins: 3
                      view_range:
                        min: 1.0
                        max: 3.0
                      x_log_scale: false
                      y_log_scale: false
                """),
            },
        },
    })
    res = yaml_repo.get_resource("YamlHist")
    gene_score = build_gene_score_from_resource(res)

    filename = gene_score.get_histogram_filename("score1")
    assert filename == "statistics/histogram_score1.yaml"


# ---------------------------------------------------------------------------
# Deprecated 'name' field in score config
# ---------------------------------------------------------------------------

def test_deprecated_name_field(caplog: pytest.LogCaptureFixture) -> None:
    deprecated_repo = build_inmemory_test_repository({
        "DeprecatedName": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: scores.csv
                scores:
                - id: my_score
                  name: my_score_col
                  desc: uses deprecated name field
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "scores.csv": textwrap.dedent("""
                gene,my_score_col
                G1,1
                G2,2
                G3,3
            """),
            "statistics": {
                "histogram_my_score.json": json.dumps({
                    "bars": [1, 1, 1],
                    "bins": [1.0, 1.665, 2.333, 3.0],
                    "config": {
                        "type": "number",
                        "number_of_bins": 3,
                        "view_range": {"min": 1.0, "max": 3.0},
                        "x_log_scale": False,
                        "y_log_scale": False,
                    },
                }),
            },
        },
    })
    res = deprecated_repo.get_resource("DeprecatedName")
    with caplog.at_level(logging.WARNING):
        gene_score = build_gene_score_from_resource(res)

    assert gene_score.get_scores() == ["my_score"]
    assert gene_score.get_gene_value("my_score", "G1") == 1.0
    assert any("deprecated" in record.message for record in caplog.records)


# ---------------------------------------------------------------------------
# Custom separator config
# ---------------------------------------------------------------------------

def test_custom_separator() -> None:
    sep_repo = build_inmemory_test_repository({
        "CustomSep": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: scores.csv
                separator: ";"
                scores:
                - id: score1
                  desc: semicolon-separated score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "scores.csv": textwrap.dedent("""
                gene;score1
                G1;10
                G2;20
                G3;30
            """),
            "statistics": {
                "histogram_score1.json": json.dumps({
                    "bars": [1, 1, 1],
                    "bins": [10.0, 16.65, 23.33, 30.0],
                    "config": {
                        "type": "number",
                        "number_of_bins": 3,
                        "view_range": {"min": 10.0, "max": 30.0},
                        "x_log_scale": False,
                        "y_log_scale": False,
                    },
                }),
            },
        },
    })
    res = sep_repo.get_resource("CustomSep")
    gene_score = build_gene_score_from_resource(res)

    assert gene_score.get_gene_value("score1", "G1") == 10.0
    assert gene_score.get_gene_value("score1", "G2") == 20.0
    assert gene_score.get_gene_value("score1", "G3") == 30.0


# ---------------------------------------------------------------------------
# small_values_desc / large_values_desc in ScoreDesc
# ---------------------------------------------------------------------------

def test_small_large_values_desc_in_score_desc() -> None:
    desc_repo = build_inmemory_test_repository({
        "DescScore": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: scores.csv
                scores:
                - id: score1
                  desc: a score with value descriptions
                  small_values_desc: "low is good"
                  large_values_desc: "high is bad"
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
                G3,3
            """),
            "statistics": {
                "histogram_score1.json": json.dumps({
                    "bars": [1, 1, 1],
                    "bins": [1.0, 1.665, 2.333, 3.0],
                    "config": {
                        "type": "number",
                        "number_of_bins": 3,
                        "view_range": {"min": 1.0, "max": 3.0},
                        "x_log_scale": False,
                        "y_log_scale": False,
                    },
                }),
            },
        },
    })
    res = desc_repo.get_resource("DescScore")
    gene_score = build_gene_score_from_resource(res)
    score_descs = GeneScoresDb.build_descs_from_score(gene_score)

    assert len(score_descs) == 1
    score_desc = score_descs[0]
    assert score_desc.small_values_desc == "low is good"
    assert score_desc.large_values_desc == "high is bad"


# ---------------------------------------------------------------------------
# GeneScoreImplementation - calc_histogram with categorical config
# ---------------------------------------------------------------------------

def test_calc_histogram_categorical() -> None:
    cat_repo = build_inmemory_test_repository({
        "CatImpl": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: cat.csv
                scores:
                - id: cat
                  desc: categorical score
                  histogram:
                    type: categorical
                    value_order: [1, 2, 3]
                """,
            "cat.csv": textwrap.dedent("""
                gene,cat
                G1,1
                G2,2
                G3,3
                G4,1
            """),
            "statistics": {
                "histogram_cat.json": json.dumps({
                    "config": {
                        "type": "categorical",
                        "value_order": [1, 2, 3],
                        "y_log_scale": False,
                        "label_rotation": 0,
                    },
                    "values": {"1": 2, "2": 1, "3": 1},
                }),
            },
        },
    })
    res = cat_repo.get_resource("CatImpl")
    gene_score = build_gene_score_from_resource(res)
    histogram = GeneScoreImplementation._calc_histogram(gene_score, "cat")

    assert isinstance(histogram, CategoricalHistogram)
    assert histogram.raw_values[1] == 2
    assert histogram.raw_values[2] == 1
    assert histogram.raw_values[3] == 1


# ---------------------------------------------------------------------------
# GeneScoreImplementation - calc_statistics_hash and calc_info_hash
# ---------------------------------------------------------------------------

def test_calc_statistics_hash(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    impl = GeneScoreImplementation(res)

    result = impl.calc_statistics_hash()

    assert isinstance(result, bytes)
    assert len(result) > 0
    parsed = json.loads(result.decode())
    assert "score_config" in parsed
    assert "score_file" in parsed
    # deterministic
    assert impl.calc_statistics_hash() == result


def test_calc_info_hash(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHist")
    impl = GeneScoreImplementation(res)

    assert impl.calc_info_hash() == b"placeholder"


# ---------------------------------------------------------------------------
# GeneScoreImplementation - create_statistics_build_tasks
# ---------------------------------------------------------------------------

def test_create_statistics_build_tasks(
    scores_repo: GenomicResourceRepo,
) -> None:
    res = scores_repo.get_resource("LinearHist")
    impl = GeneScoreImplementation(res)

    tasks = impl.create_statistics_build_tasks()

    # LinearHist has 1 score → 2 tasks (calc + save)
    assert len(tasks) == 1
    assert all(isinstance(t, TaskDesc) for t in tasks)


def test_int_scores(scores_repo: GenomicResourceRepo) -> None:
    res = scores_repo.get_resource("LinearHistInt")
    gene_score = build_gene_score_from_resource(res)

    assert gene_score.get_gene_value("int score", "G1") == 1
    assert gene_score.get_gene_value("int score", "G2") == 2
    assert gene_score.get_gene_value("int score", "G3") == 3

    assert gene_score.score_definitions["int score"].value_type == "int"
