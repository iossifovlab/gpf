# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest
from gain.annotation.annotation_pipeline import AnnotatorInfo, AttributeInfo
from gain.annotation.gene_score_annotator import GeneScoreAnnotator
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from gain.genomic_resources.testing import build_inmemory_test_repository


@pytest.fixture
def scores_repo() -> GenomicResourceRepo:
    return build_inmemory_test_repository({
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
            """),
        },
        "int_score": {
            GR_CONF_FILE_NAME: """
                type: gene_score
                filename: int.csv
                scores:
                  - id: int_score
                    desc: test integer score
                    type: int
                    histogram:
                      type: number
                      number_of_bins: 6
                      x_log_scale: false
                      y_log_scale: false
                """,
            "int.csv": textwrap.dedent("""
                gene,int_score
                G1,1
                G2,2
                G3,3
                G4,4
                G5,5
                G6,6
            """),
        },
    })


def test_gene_score_annotator(scores_repo: GenomicResourceRepo) -> None:
    resource = scores_repo.get_resource("LGD_rank")
    annotator = GeneScoreAnnotator(
        None,
        AnnotatorInfo(
            "gosho",
            [AttributeInfo(
                "LGD_rank",
                "LGD_rank",
                internal=False,
                parameters={"gene_aggregator": "min"})],
            {},
        ),
        resource,
        "gene_list",
    )

    result = annotator.annotate(None, {"gene_list": ["LRP1", "TRRAP"]})

    assert result == {"LGD_rank": 1}


def test_gene_score_annotator_int_attributes(
    scores_repo: GenomicResourceRepo,
) -> None:
    resource = scores_repo.get_resource("int_score")
    annotator = GeneScoreAnnotator(
        None,
        AnnotatorInfo(
            "gosho",
            [AttributeInfo(
                "int_score",
                "int_score",
                internal=False,
                parameters={"gene_aggregator": "min"})],
            {},
        ),
        resource,
        "gene_list",
    )

    attribute_descs = annotator.get_all_attribute_descriptions()

    assert attribute_descs["int_score"].type == "int"

    result = annotator.annotate(None, {"gene_list": ["G2"]})

    assert result == {"int_score": 2}


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


def test_gene_score_annotator_used_context_attributes(
    scores_repo: GenomicResourceRepo,
) -> None:
    resource = scores_repo.get_resource("LGD_rank")
    annotator = GeneScoreAnnotator(
        None,
        AnnotatorInfo(
            "gosho",
            [AttributeInfo(
                "LGD_rank",
                "LGD_rank",
                internal=False,
                parameters={"gene_aggregator": "min"})],
            {},
        ),
        resource,
        "gene_list",
    )
    assert annotator.used_context_attributes == ("gene_list",)
