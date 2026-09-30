# pylint: disable=W0621,C0114,C0116,W0212,W0613,W0104
import json
import textwrap

import pytest
from gain.gene_scores.gene_scores import build_gene_score_from_resource
from gain.genomic_resources.histogram import (
    CategoricalHistogram,
    NumberHistogram,
)
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from gain.genomic_resources.testing import build_inmemory_test_repository

from gpf.gene_scores import GeneScoreDesc, GeneScoresDb


def _number_histogram_json(
    bars: list[int], bins: list[float], view_range: tuple[float, float],
) -> str:
    return textwrap.dedent(f"""{{
        "bars": {bars},
        "bins": {bins},
        "config": {{
          "type": "number",
          "number_of_bins": {len(bars)},
          "view_range": {{"min": {view_range[0]}, "max": {view_range[1]}}},
          "x_log_scale": false,
          "y_log_scale": false
        }}
    }}""")


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
                "histogram_linear score.json": _number_histogram_json(
                    [2, 2, 2], [1.0, 1.665, 2.333, 3.0], (1.0, 3.0)),
            },
        },
        "RVIS_rank": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: RVIS.csv
                scores:
                  - id: RVIS_rank
                    desc: RVIS rank
                    histogram:
                      type: number
                      number_of_bins: 150
                      x_log_scale: false
                      y_log_scale: false
                """,
            "RVIS.csv": textwrap.dedent("""
                "gene","RVIS","RVIS_rank"
                "LRP1",-7.28,3
                "TRRAP",-6.14,6
                "ANKRD11",-4.38,15
                "UBR4",-7.5,2
                "NOTCH1",-3.51,55
                """),
        },
        "LGD_rank": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: LGD.csv
                scores:
                  - id: LGD_rank
                    desc: LGD rank
                    histogram:
                      type: number
                      number_of_bins: 150
                      x_log_scale: false
                      y_log_scale: false
                """,
            "LGD.csv": textwrap.dedent("""
                "gene","LGD_score","LGD_rank"
                "LRP1",0.000014,1
                "TRRAP",0.00016,3
                "ANKRD11",0.0004,5
                "SPTBN1",0.002715,19.5
                "UBR4",0.007496,59
            """),
        },
    })


@pytest.fixture
def gene_scores_db(scores_repo: GenomicResourceRepo) -> GeneScoresDb:
    return GeneScoresDb([
        build_gene_score_from_resource(scores_repo.get_resource(resource_id))
        for resource_id in ["LGD_rank", "RVIS_rank"]
    ])


def test_build_descs_from_score_describes_each_score(
    scores_repo: GenomicResourceRepo,
) -> None:
    gene_score = build_gene_score_from_resource(
        scores_repo.get_resource("LinearHist"))

    (score_desc,) = GeneScoresDb.build_descs_from_score(gene_score)

    assert isinstance(score_desc, GeneScoreDesc)
    assert score_desc.resource_id == "LinearHist"
    assert score_desc.score_id == "linear score"
    assert score_desc.column_name == "linear_score"
    assert score_desc.value_type == "float"
    assert score_desc.description == "linear gene score"
    assert isinstance(score_desc.hist, NumberHistogram)
    assert score_desc.hist.bars.tolist() == [2, 2, 2]
    assert score_desc.small_values_desc is None
    assert score_desc.large_values_desc is None


def test_score_desc_help_is_the_gene_score_help(
    scores_repo: GenomicResourceRepo,
) -> None:
    gene_score = build_gene_score_from_resource(
        scores_repo.get_resource("LinearHist"))

    (score_desc,) = GeneScoresDb.build_descs_from_score(gene_score)

    assert score_desc.help == gene_score.build_score_help("linear score")
    assert '<div class="score-description">' in score_desc.help


def test_score_desc_carries_small_and_large_values_desc() -> None:
    repo = build_inmemory_test_repository({
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
                "histogram_score1.json": _number_histogram_json(
                    [1, 1, 1], [1.0, 1.665, 2.333, 3.0], (1.0, 3.0)),
            },
        },
    })
    gene_score = build_gene_score_from_resource(
        repo.get_resource("DescScore"))

    (score_desc,) = GeneScoresDb.build_descs_from_score(gene_score)

    assert score_desc.small_values_desc == "low is good"
    assert score_desc.large_values_desc == "high is bad"


def test_db_indexes_descs_by_score_id(gene_scores_db: GeneScoresDb) -> None:
    assert gene_scores_db.get_score_ids() == ["LGD_rank", "RVIS_rank"]
    assert len(gene_scores_db) == 2
    assert "RVIS_rank" in gene_scores_db
    assert "bad_score" not in gene_scores_db
    assert gene_scores_db["RVIS_rank"].description == "RVIS rank"


def test_getitem_of_a_missing_score_raises(
    gene_scores_db: GeneScoresDb,
) -> None:
    with pytest.raises(ValueError, match="score bad_score not found"):
        gene_scores_db["bad_score"]


def test_get_score_desc(gene_scores_db: GeneScoresDb) -> None:
    score_desc = gene_scores_db.get_score_desc("LGD_rank")

    assert score_desc is not None
    assert score_desc.resource_id == "LGD_rank"
    assert gene_scores_db.get_score_desc("bad_score") is None
    assert sorted(d.score_id for d in gene_scores_db.get_scores()) == [
        "LGD_rank", "RVIS_rank",
    ]


def test_gene_scores_are_indexed_by_resource_id(
    scores_repo: GenomicResourceRepo,
) -> None:
    gene_score = build_gene_score_from_resource(
        scores_repo.get_resource("LinearHist"))

    db = GeneScoresDb([gene_score])

    assert db.get_gene_score_ids() == ["LinearHist"]
    assert db.get_gene_scores() == [gene_score]
    assert db.get_gene_score("LinearHist") is gene_score
    assert db.get_gene_score("linear score") is None
    assert db.get_score_ids() == ["linear score"]


def test_empty_db() -> None:
    db = GeneScoresDb([])

    assert len(db) == 0
    assert not db.get_score_ids()
    assert not db.get_gene_score_ids()
    assert not db.get_gene_scores()
    assert not db.get_scores()
    assert "anything" not in db


def test_score_desc_carries_a_categorical_histogram() -> None:
    repo = build_inmemory_test_repository({
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
    gene_score = build_gene_score_from_resource(repo.get_resource("CatScore"))

    (score_desc,) = GeneScoresDb.build_descs_from_score(gene_score)

    assert isinstance(score_desc.hist, CategoricalHistogram)
    assert score_desc.hist.raw_values == {"1": 1, "2": 1, "3": 1}


def test_a_resource_with_several_scores_contributes_each() -> None:
    repo = build_inmemory_test_repository({
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
                "histogram_score1.json": _number_histogram_json(
                    [1, 1, 1], [1.0, 1.665, 2.333, 3.0], (1.0, 3.0)),
                "histogram_score2.json": _number_histogram_json(
                    [1, 1, 1], [10.0, 16.65, 23.33, 30.0], (10.0, 30.0)),
            },
        },
    })
    gene_score = build_gene_score_from_resource(
        repo.get_resource("MultiScore"))

    db = GeneScoresDb([gene_score])

    assert db.get_score_ids() == ["score1", "score2"]
    assert db.get_gene_score_ids() == ["MultiScore"]
    assert {d.resource_id for d in db.get_scores()} == {"MultiScore"}
