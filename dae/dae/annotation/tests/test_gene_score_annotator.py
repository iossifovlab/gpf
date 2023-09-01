# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pathlib

import pytest

from dae.annotation.annotation_pipeline import AnnotatorInfo, AttributeInfo
from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    GenomicResourceRepo
from dae.annotation.gene_score_annotator import GeneScoreAnnotator


@pytest.fixture
def scores_repo(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    scores_repo = build_inmemory_test_repository({
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
                "ZFHX3",0.000925,8
                "HERC2",0.003682,25
                "TRIO",0.001563,11
                "MACF1",0.000442,6
                "PLEC",0.004842,40
                "SRRM2",0.004471,35
                "SPTBN1",0.002715,19.5
                "UBR4",0.007496,59
            """)
        }
    })
    return scores_repo


def test_gene_score_annotator(scores_repo: GenomicResourceRepo) -> None:
    resource = scores_repo.get_resource("LGD_rank")
    annotator = GeneScoreAnnotator(
        None, AnnotatorInfo("gosho",
                            [AttributeInfo("LGD_rank", "LGD_rank", False,
                                           {"gene_aggregator": "min"})],
                            {}),
        resource, "gene_list")

    result = annotator.annotate(None, {"gene_list": ["LRP1", "TRRAP"]})

    assert result == {"LGD_rank": 1}


def test_gene_score_annotator_default_aggregator(
        scores_repo: GenomicResourceRepo) -> None:
    resource = scores_repo.get_resource("LGD_rank")
    annotator = GeneScoreAnnotator(None,
                                   AnnotatorInfo("gosho", [], {}),
                                   resource, "gene_list")

    result = annotator.annotate(None, {"gene_list": ["LRP1", "TRRAP"]})

    assert result == {"LGD_rank": {"LRP1": 1, "TRRAP": 3}}


def test_gene_score_annotator_resources(
        scores_repo: GenomicResourceRepo) -> None:
    resource = scores_repo.get_resource("LGD_rank")
    annotator = GeneScoreAnnotator(None,
                                   AnnotatorInfo("gosho", [], {}),
                                   resource, "gene_list")

    assert annotator.resource_ids == {"LGD_rank"}
