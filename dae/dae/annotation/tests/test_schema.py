import pytest
import textwrap

from dae.genomic_resources import build_genomic_resource_repository
from dae.annotation.annotation_factory import build_annotation_pipeline


@pytest.fixture
def genomic_resources_repo():
    repo = build_genomic_resource_repository({
        "id": "test_annotation",
        "type": "embeded",
        "content": {
            "position_score1": {
                "genomic_resource.yaml":
                """\
                type: PositionScore
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
                    attributes:
                    - source: test100way
                      destination: test100
                    - source: t1
                      destination: t1
                    - source: t2
                      destination: t2
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
                type: NPScore
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
        }
    })

    return repo


def test_annotation_pipeline_schema_basics(genomic_resources_repo):

    pipeline_config = textwrap.dedent("""
        - np_score:
            resource_id: np_score1
            attributes:
            - source: test_raw
              destination: test
        - position_score:
            resource_id: position_score1
        """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=genomic_resources_repo)

    assert pipeline is not None

    assert len(pipeline.annotators) == 2

    schema = pipeline.annotation_schema
    assert len(schema) == 4

    assert "test100" in schema


def test_annotation_pipeline_schema_with_internal(genomic_resources_repo):

    pipeline_config = textwrap.dedent("""
        - np_score:
            resource_id: np_score1
            attributes:
            - source: test_raw
              destination: test
        - position_score:
            resource_id: position_score1
            attributes:
            - source: test100way
              destination: test100way
            - source: t1
              internal: True
        """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=genomic_resources_repo)

    assert pipeline is not None

    assert len(pipeline.annotators) == 2

    schema = pipeline.annotation_schema
    assert len(schema) == 3, schema

    assert len(schema.public_fields) == 2
    assert "t1" in schema
    assert "t1" not in schema.public_fields
    assert "t1" in schema.internal_fields

    assert "test100way" in schema
    assert "test100way" in schema.public_fields
    assert "test100way" not in schema.internal_fields


def test_annotation_pipeline_liftover_annotator_schema(grr_fixture):

    pipeline_config = textwrap.dedent("""
    - liftover_annotator:
        chain: hg38/hg38tohg19
        target_genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
    """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=grr_fixture)

    assert pipeline is not None

    assert len(pipeline.annotators) == 1
    print(100*"=")
    print(pipeline.annotation_schema)
    print(100*"=")

    schema = pipeline.annotation_schema
    assert len(schema) == 1
    assert "liftover_annotatable" in schema

    assert schema["liftover_annotatable"].internal is True
    assert schema["liftover_annotatable"].type == "object"

    assert "liftover_annotatable" not in schema.public_fields
    assert "liftover_annotatable" in schema.internal_fields


def test_annotation_pipeline_effect_annotator_schema(grr_fixture):

    pipeline_config = textwrap.dedent("""
    - effect_annotator:
        genome: hg38/GRCh38-hg38/genome
        gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
    """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=grr_fixture)

    assert pipeline is not None

    assert len(pipeline.annotators) == 1
    print(100*"=")
    print(pipeline.annotation_schema)
    print(100*"=")

    schema = pipeline.annotation_schema
    assert len(schema) == 4, schema

    assert "allele_effects" in schema
    assert "allele_effects" in schema.internal_fields
    assert "allele_effects" not in schema.public_fields

    assert "effect_type" in schema
    assert "effect_type" in schema.public_fields
    assert "effect_type" not in schema.internal_fields
