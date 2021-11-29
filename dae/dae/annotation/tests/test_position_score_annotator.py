import pytest
import textwrap

from dae.annotation.annotatable import VCFAllele
from dae.genomic_resources import build_genomic_resource_repository

from dae.annotation.annotation_pipeline import AnnotationConfigParser, \
    AnnotationPipeline


@pytest.fixture
def position_score_repo():
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
            }
        }
    })

    return repo


def test_position_resource_default_annotation(position_score_repo):

    res = position_score_repo.get_resource("position_score1")
    assert res is not None

    default_annotation = res.get_default_annotation()
    print(default_annotation)

    assert "attributes" in default_annotation


#  hg19
#  chrom: 1
#  pos:   14970
#
#  T     A     C     C    C    T    T    G    C    G
#  67    68    69    70   71   72   73   74   75   76
#  0.02  0.01  0.01  0.1  0.1  0.2  0.2  0.3  0.3  0.4
#

# TODO: Add test for complex
@pytest.mark.parametrize("allele,pos_aggregator, expected", [
    (("1", 14970, "C", "A"),   "mean", 0.1),

    (("1", 14970, "CC", "C"),  "mean", (0.1 + 0.1 + 0.2)/3),
    (("1", 14970, "CC", "C"),  "max", 0.2),

    (("1", 14970, "CCT", "C"), "mean", (0.1 + 0.1 + 0.2 + 0.2) / 4),
    (("1", 14970, "CCT", "C"), "max", 0.2),

    (("1", 14970, "C", "CA"),  "mean", 0.1),
    (("1", 14970, "C", "CAA"), "mean", 0.1),
    (("1", 14970, "C", "CAA"), "max", 0.1),

    (("1", 14971, "C", "CA"),  "mean", (0.1 + 0.2) / 2),
    (("1", 14971, "C", "CA"),  "max", 0.2),

    (("1", 14971, "C", "CAA"), "mean", (0.1 + 0.2) / 2),
    (("1", 14971, "C", "CAA"), "max", 0.2),
])
def test_position_score_annotator(
        allele, pos_aggregator, expected, position_score_repo):

    annotatable = VCFAllele(*allele)

    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent(f"""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
                  position_aggregator: {pos_aggregator}
            """)
    )

    pipeline = AnnotationPipeline.build(
        pipeline_config, grr_repository=position_score_repo)
    # annoation_runner = BasicAnnotatorRunner()
    # annotator = ThreadAnnotatorRunner()
    # annotator = AsynioAnnotatorRunner()

    # result = annotation_runner.run(pipeline, annotatable)

    result = pipeline.annotate(annotatable)

    print(annotatable, result)
    assert result.get("test100") == expected


def test_position_annotator_schema(position_score_repo):
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
            """)
    )

    pipeline = AnnotationPipeline.build(pipeline_config,
                                        grr_repository=position_score_repo)
    schema = pipeline.annotation_schema

    assert len(schema) == 1
    assert schema.names == ["test100"]
    field = schema["test100"]
    assert field.name == "test100"
    # FIXME: assert field.type == float
    assert field.source.annotator_type == "position_score"
    assert field.source.resource_id == "position_score1"
    assert field.source.score_id == "test100way"


def test_position_default_annotator_schema(position_score_repo):
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - position_score:
                resource_id: position_score1
            """)
    )

    pipeline = AnnotationPipeline.build(
        pipeline_config, grr_repository=position_score_repo)
    assert len(pipeline.annotation_schema) == 3
    schema = pipeline.annotation_schema

    assert schema.names == ["test100", "t1", "t2"]

    field = schema["t1"]
    assert field.name == "t1"
    # FIXME: assert field.type == float
    assert field.source.annotator_type == "position_score"
    assert field.source.resource_id == "position_score1"
    assert field.source.score_id == "t1"


def test_position_annotator_schema_one_source_two_dest(position_score_repo):
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
                - source: test100way
                  destination: test100max
                  position_aggregator: max
            """)
    )

    pipeline = AnnotationPipeline.build(
        pipeline_config, grr_repository=position_score_repo)
    schema = pipeline.annotation_schema

    assert len(schema) == 2
    assert schema.names == ["test100", "test100max"]

    field = schema["test100"]
    assert field.name == "test100"
    # FIXME: assert field.type == float
    assert field.source.annotator_type == "position_score"
    assert field.source.resource_id == "position_score1"
    assert field.source.score_id == "test100way"

    field = schema["test100max"]
    assert field.name == "test100max"
    # FIXME: assert field.type == float
    assert field.source.annotator_type == "position_score"
    assert field.source.resource_id == "position_score1"
    assert field.source.score_id == "test100way"


def test_position_annotator_join_aggregation(position_score_repo):
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
                  position_aggregator: join(, )
            """)
    )
    print(pipeline_config)

    pipeline = AnnotationPipeline.build(
      pipeline_config=pipeline_config, grr_repository=position_score_repo)
    allele = ("1", 14970, "CC", "C")
    annotatable = VCFAllele(*allele)
    result = pipeline.annotate(annotatable)

    assert result.get("test100") == "0.1, 0.1, 0.2"
