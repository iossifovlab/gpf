import tempfile
import shutil

import pytest

from dae.gene.scores import GenomicScoresDb
from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.fixture
def temp_cache_dir(request):
    dirname = tempfile.mkdtemp(suffix="_scores", prefix="cache_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)

    return dirname


@pytest.fixture(scope="session")
def scores_repo():
    sets_repo = GenomicResourceEmbededRepo("gene_sets", content={
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
                "    desc: \"phastCons100 desc\"\n"
                "histograms:\n"
                " - score: phastCons100\n"
                "   bins: 100\n"
                "   xscale: linear\n"
                "   yscale: linear\n"
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


def test_genomic_scores_db(scores_repo, temp_cache_dir):
    db = GenomicScoresDb(
        scores_repo,
        [("phastCons", "phastCons100")],
        temp_cache_dir
    )
    assert len(db.get_scores()) == 1
    assert "phastCons100" in db
    assert db["phastCons100"] is not None

    score = db["phastCons100"]
    assert score.id == "phastCons100"
    assert score.desc == "phastCons100 desc"
    assert len(score.bars) == 11
    assert len(score.bins) == 11
    assert score.xscale == "linear"
    assert score.yscale == "linear"
    assert score.help == "test_help"