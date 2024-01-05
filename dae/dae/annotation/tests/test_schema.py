# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.annotation.annotation_factory import build_annotation_pipeline


@pytest.fixture
def genomic_resources_repo() -> GenomicResourceRepo:
    repo = build_inmemory_test_repository({
        "position_score1": {
            "genomic_resource.yaml":
            """\
            type: position_score
            table:
              filename: data.mem
            scores:
            - id: test100way
              type: float
              desc: "test values"
              name: 100way
            - id: t1
              type: float
              desc: "test score 1"
              name: t1
            - id: t2
              type: float
              desc: "test score 2"
              name: t2
            default_annotation:
            - source: test100way
              name: test100
            - source: t1
              name: t1
            - source: t2
              name: t2
            """,
            "data.mem": """
                chrom  pos_begin  pos_end  100way   t1   t2
                1      14966      14967    0.02     -2   -20
                1      14968      14969    0.01     -1   -10
                1      14970      14971    0.1      1    10
                1      14972      14973    0.2      2    20
                1      14974      14975    0.3      3    30
                1      14976      14977    0.4      4    40
            """
        },
        "np_score1": {
            "genomic_resource.yaml":
            """\
            type: np_score
            table:
                filename: data.mem
            scores:
            - id: test_raw
              type: float
              desc: "test values"
              name: raw
            """,
            "data.mem": """
                chrom  pos_begin  reference alternative raw
                1      14968      A         C           0.00001
                1      14968      A         G           0.00002
                1      14968      A         T           0.00004
                1      14969      C         A           0.0001
                1      14969      C         G           0.0002
                1      14969      C         T           0.0004
                1      14970      C         A           0.001
                1      14970      C         G           0.002
                1      14970      C         T           0.004
                1      14971      C         A           0.01
                1      14971      C         G           0.02
                1      14971      C         T           0.04
                1      14972      T         A           0.1
                1      14972      T         C           0.2
                1      14972      T         G           0.4
            """
        }
    })

    return repo


def test_annotation_pipeline_schema_basics(
        genomic_resources_repo: GenomicResourceRepo) -> None:
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
        - np_score:
            resource_id: np_score1
            attributes:
            - source: test_raw
              name: test
        - position_score:
            resource_id: position_score1
        """, grr_repository=genomic_resources_repo)

    assert len(pipeline.annotators) == 2
    assert len(pipeline.get_attributes()) == 4
    assert pipeline.get_attribute_info("test100") is not None


def test_annotation_pipeline_schema_with_internal(
        genomic_resources_repo: GenomicResourceRepo) -> None:

    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
        - np_score:
            resource_id: np_score1
            attributes:
            - name: test
              source: test_raw
        - position_score:
            resource_id: position_score1
            attributes:
            - test100way
            - name: t1
              internal: True
        """, grr_repository=genomic_resources_repo)

    assert len(pipeline.annotators) == 2

    assert len(pipeline.get_attributes()) == 3

    att = pipeline.get_attribute_info("t1")
    assert att is not None
    assert att.internal

    att = pipeline.get_attribute_info("test100way")
    assert att is not None
    assert not att.internal
