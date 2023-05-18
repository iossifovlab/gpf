# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pytest

from dae.annotation.annotatable import VCFAllele
from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.annotation.gene_score_annotator import GeneScoreAnnotator


@pytest.fixture
def scores_repo(tmp_path):
    scores_repo = build_inmemory_test_repository({
        "LGD_rank": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: LGD.csv
                gene_scores:
                  - id: LGD_rank
                    desc: LGD rank
                histograms:
                  - score: LGD_rank
                    bins: 150
                    x_scale: linear
                    y_scale: linear
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


def test_gene_score_annotator(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    config = {
        "annotator_type": "gene_score_annotator",
        "resource_id": "LGD_rank",
        "input_gene_list": "gene_list",
        "attributes": [
            {
                "source": "LGD_rank",
                "destination": "LGD_rank",
                "gene_aggregator": "dict"
            },
        ]
    }

    annotator = GeneScoreAnnotator(config, resource)
    annotatable = VCFAllele("1", 1, "T", "G")
    context = {"gene_list": ["LRP1", "TRRAP"]}
    result = annotator._do_annotate(annotatable, context)
    assert result == {"LGD_rank": {"LRP1": 1, "TRRAP": 3}}


def test_gene_score_annotator_default_aggregator(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    config = {
        "annotator_type": "gene_score_annotator",
        "resource_id": "LGD_rank",
        "input_gene_list": "gene_list",
        "attributes": [
            {
                "source": "LGD_rank",
                "destination": "LGD_rank",
            },
        ]
    }

    annotator = GeneScoreAnnotator(config, resource)
    annotatable = VCFAllele("1", 1, "T", "G")
    context = {"gene_list": ["LRP1", "TRRAP"]}
    result = annotator._do_annotate(annotatable, context)
    assert result == {"LGD_rank": {"LRP1": 1, "TRRAP": 3}}


def test_gene_score_annotator_resources(scores_repo):
    resource = scores_repo.get_resource("LGD_rank")
    config = {
        "annotator_type": "gene_score_annotator",
        "resource_id": "LGD_rank",
        "input_gene_list": "gene_list",
        "attributes": [
            {
                "source": "LGD_rank",
                "destination": "LGD_rank",
                "gene_aggregator": "dict"
            },
        ]
    }

    annotator = GeneScoreAnnotator(config, resource)
    assert {res.get_id() for res in annotator.resources} == {"LGD_rank"}
