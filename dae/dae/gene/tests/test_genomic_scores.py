# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models, setup_gpf_instance

from dae.gene.scores import GenomicScoresDb
from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.fixture
def scores_repo(tmp_path):
    sets_repo = build_inmemory_test_repository({
        "phastCons": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: position_score
                table:
                  filename: phastCons100.bedGraph.gz
                  format: tabix
                  header_mode: none
                  chrom:
                    index: 0
                  pos_begin:
                    index: 1
                  pos_end:
                    index: 2
                scores:
                  - id: phastCons100
                    index: 3
                    type: float
                    desc: phastCons100 desc
                histograms:
                 - score: phastCons100
                   bins: 100
                   min: 1574474507.0
                   max: 23092042.0
                   x_scale: linear
                   y_scale: linear
                default_annotation:
                  attributes:
                    - source: phastCons100
                      destination: phastcons100
                meta:
                  description:
                    test_help
                  labels: ~
            """),
            "histograms": {
                "phastCons100.csv": textwrap.dedent("""
                    bars,bins
                    1574474507.0,0.0
                    270005746.0,0.01
                    116838135.0,0.02
                    85900783.0,0.03
                    68361899.0,0.04
                    48385988.0,0.05
                    39892532.0,0.06
                    33851345.0,0.07
                    26584576.0,0.08
                    28626413.0,0.09
                    23092042.0,0.1
                """)
            }
        }
    })
    return sets_repo


def test_genomic_scores_db(scores_repo):
    db = GenomicScoresDb(
        scores_repo,
        [("phastCons", "phastcons100")]
    )
    assert len(db.get_scores()) == 1
    assert "phastcons100" in db
    assert db["phastcons100"] is not None

    score = db["phastcons100"]
    assert len(score.hist.bars) == 11
    assert len(score.hist.bins) == 11
    assert score.hist.config.x_scale == "linear"
    assert score.hist.config.y_scale == "linear"


@pytest.fixture
def annotation_gpf(scores_repo, tmp_path_factory):
    root_path = tmp_path_factory.mktemp("genomic_scores_db_gpf")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        annotation:
            conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
        - position_score: phastCons
        """)
    })
    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
        grr=scores_repo
    )
    return gpf_instance


def test_genomic_scores_db_with_annotation(annotation_gpf):
    assert annotation_gpf is not None
    annotaiton_pipeline = annotation_gpf.get_annotation_pipeline()
    assert annotaiton_pipeline is not None

    db = annotation_gpf.genomic_scores_db
    assert db is not None
    assert len(db.get_scores()) == 1
    assert "phastcons100" in db
    assert db["phastcons100"] is not None

    score = db["phastcons100"]
    assert len(score.hist.bars) == 11
    assert len(score.hist.bins) == 11
    assert score.hist.config.x_scale == "linear"
    assert score.hist.config.y_scale == "linear"
