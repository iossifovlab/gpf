# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.gene.scores import GenomicScoresDb
from dae.genomic_resources.testing import build_testing_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.fixture(scope="session")
def scores_repo():
    sets_repo = build_testing_repository(repo_id="gene_sets", content={
        "phastCons": {
            GR_CONF_FILE_NAME: (
                "type: position_score\n"
                "table:\n"
                "  filename: phastCons100.bedGraph.gz\n"
                "  format: tabix\n"
                "  header_mode: none\n"
                "  chrom:\n"
                "    index: 0\n"
                "  pos_begin:\n"
                "    index: 1\n"
                "  pos_end:\n"
                "    index: 2\n"
                "scores:\n"
                "  - id: phastCons100\n"
                "    index: 3\n"
                "    type: float\n"
                "    desc: \'phastCons100 desc\'\n"
                "histograms:\n"
                " - score: phastCons100\n"
                "   bins: 100\n"
                "   min: 1574474507.0\n"
                "   max: 23092042.0\n"
                "   x_scale: linear\n"
                "   y_scale: linear\n"
                "default_annotation:\n"
                "  attributes:\n"
                "    - source: phastCons100\n"
                "      destination: phastCons100\n"
                "meta:\n"
                "  test_help"
            ),
            "histograms": {
                "phastCons100.csv": (
                    "bars,bins\n"
                    "1574474507.0,0.0\n"
                    "270005746.0,0.01\n"
                    "116838135.0,0.02\n"
                    "85900783.0,0.03\n"
                    "68361899.0,0.04\n"
                    "48385988.0,0.05\n"
                    "39892532.0,0.06\n"
                    "33851345.0,0.07\n"
                    "26584576.0,0.08\n"
                    "28626413.0,0.09\n"
                    "23092042.0,0.1\n"
                )
            }
        }
    })
    return sets_repo


def test_genomic_scores_db(scores_repo):
    db = GenomicScoresDb(
        scores_repo,
        [("phastCons", "phastCons100")]
    )
    assert len(db.get_scores()) == 1
    assert "phastCons100" in db
    assert db["phastCons100"] is not None

    score = db["phastCons100"]
    assert len(score.bars) == 11
    assert len(score.bins) == 11
    assert score.x_scale == "linear"
    assert score.y_scale == "linear"
