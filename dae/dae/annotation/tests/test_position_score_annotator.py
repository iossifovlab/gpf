# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme
import pathlib
import textwrap
import pytest

from dae.annotation.annotatable import VCFAllele
from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.genomic_scores import \
    PositionScore
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.genomic_resources.testing import \
    build_filesystem_test_repository, \
    setup_directories, setup_tabix


@pytest.fixture
def position_score_repo() -> GenomicResourceRepo:
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
    })

    return repo


def test_position_resource_default_annotation(
        position_score_repo: GenomicResourceRepo) -> None:

    res = position_score_repo.get_resource("position_score1")
    assert res is not None
    score = PositionScore(res)

    default_annotation = score.get_default_annotation_attributes()

    assert len(default_annotation) == 3


def test_position_score_annotator_all_attributes(
        position_score_repo: GenomicResourceRepo) -> None:

    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
                  position_aggregator: max
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    annotator = pipeline.annotators[0]
    assert len(annotator.attributes) == 1

    attribute = annotator.attributes[0]

    assert attribute.name == "test100"
    assert attribute.type == "float"
    assert attribute.description == "test values"


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
    (("1", 14970, "C", "A"), "mean", 0.1),

    (("1", 14970, "CC", "C"), "mean", (0.1 + 0.1 + 0.2) / 3),
    (("1", 14970, "CC", "C"), "max", 0.2),

    (("1", 14970, "CCT", "C"), "mean", (0.1 + 0.1 + 0.2 + 0.2) / 4),
    (("1", 14970, "CCT", "C"), "max", 0.2),

    (("1", 14970, "C", "CA"), "mean", 0.1),
    (("1", 14970, "C", "CAA"), "mean", 0.1),
    (("1", 14970, "C", "CAA"), "max", 0.1),

    (("1", 14971, "C", "CA"), "mean", (0.1 + 0.2) / 2),
    (("1", 14971, "C", "CA"), "max", 0.2),

    (("1", 14971, "C", "CAA"), "mean", (0.1 + 0.2) / 2),
    (("1", 14971, "C", "CAA"), "max", 0.2),
])
def test_position_score_annotator(
        allele: tuple, pos_aggregator: str, expected: float,
        position_score_repo: GenomicResourceRepo) -> None:

    annotatable = VCFAllele(*allele)

    pipeline_config = textwrap.dedent(f"""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
                  position_aggregator: {pos_aggregator}
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    # annoation_runner = BasicAnnotatorRunner()
    # annotator = ThreadAnnotatorRunner()
    # annotator = AsynioAnnotatorRunner()

    # result = annotation_runner.run(pipeline, annotatable)
    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

        print(annotatable, result)
        assert result.get("test100") == expected


def test_position_annotator_info(
        position_score_repo: GenomicResourceRepo) -> None:
    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    pipeline_info = pipeline.get_info()
    assert len(pipeline_info) == 1
    annotator_info = pipeline_info[0]
    assert len(annotator_info.attributes) == 1
    attribute_info = annotator_info.attributes[0]

    assert annotator_info.type == "position_score"
    assert annotator_info.parameters["resource_id"] == "position_score1"

    assert attribute_info.name == "test100"
    assert attribute_info.type == "float"
    assert attribute_info.source == "test100way"

    attributes2 = pipeline.get_attributes()
    assert len(attributes2) == 1
    assert attributes2[0] == attribute_info


def test_position_default_annotator_schema(
        position_score_repo: GenomicResourceRepo) -> None:
    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    attributes = pipeline.get_attributes()
    assert [att.name for att in attributes] == ["test100", "t1", "t2"]


def test_position_annotator_schema_one_source_two_dest_schema(
        position_score_repo: GenomicResourceRepo) -> None:
    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
                - source: test100way
                  destination: test100max
                  position_aggregator: max
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    assert len(pipeline.get_info()) == 1
    annotator_info = pipeline.get_info()[0]
    assert annotator_info.type == "position_score"
    assert annotator_info.parameters["resource_id"] == "position_score1"

    attributes = pipeline.get_attributes()
    assert len(attributes) == 2

    assert attributes[0].name == "test100"
    assert attributes[0].source == "test100way"
    assert attributes[0].type == "float"
    assert attributes[0].description == "test values"

    assert attributes[1].name == "test100max"
    assert attributes[1].source == "test100way"
    assert attributes[1].type == "float"
    assert attributes[1].description == "test values"


def test_position_annotator_join_aggregation(
        position_score_repo: GenomicResourceRepo) -> None:
    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100
                  position_aggregator: join(, )
            """)
    print(pipeline_config)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    with pipeline.open() as work_pipeline:
        allele = ("1", 14970, "CC", "C")
        annotatable = VCFAllele(*allele)
        result = work_pipeline.annotate(annotatable)

    assert result.get("test100") == "0.1, 0.1, 0.2"


def test_position_annotator_schema_one_source_two_dest_annotate(
        position_score_repo: GenomicResourceRepo) -> None:
    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100min
                  position_aggregator: min
                - source: test100way
                  destination: test100max
                  position_aggregator: max
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    with pipeline.open() as work_pipeline:
        allele = VCFAllele("1", 14971, "C", "CAA")
        result = work_pipeline.annotate(allele)

    assert "test100min" in result
    assert "test100max" in result
    assert len(result) == 2

    assert result["test100min"] == 0.1
    assert result["test100max"] == 0.2


def test_position_score_annotator_attributes_with_aggr_fails(
        position_score_repo: GenomicResourceRepo) -> None:
    with pytest.raises(ValueError) as error:
        build_annotation_pipeline(pipeline_config_str="""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100min
                  position_aggregator: min
                  nucleotide_aggregator: mean
        """, grr_repository=position_score_repo)
    assert "nucleotide_aggregator" in str(error)


def test_position_score_annotator_invalid_aggregator(
        position_score_repo: GenomicResourceRepo) -> None:
    with pytest.raises(ValueError) as error:
        build_annotation_pipeline(pipeline_config_str="""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100min
                  position_aggregator: minn
        """, grr_repository=position_score_repo)
    assert "minn" in str(error)


def test_position_annotator_documentation(
        position_score_repo: GenomicResourceRepo) -> None:
    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  destination: test100min
                  position_aggregator: min
                - source: test100way
                  destination: test100max
                  position_aggregator: max
                - source: test100way
                  destination: test100default
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=position_score_repo)

    att1 = pipeline.get_attribute_info("test100min")
    assert att1 is not None
    assert "min" in att1.documentation

    att2 = pipeline.get_attribute_info("test100max")
    assert att2 is not None
    assert "max" in att2.documentation

    att3 = pipeline.get_attribute_info("test100default")
    assert att3 is not None
    assert "default" in att3.documentation


@pytest.mark.parametrize("allele, expected", [
    (("chr1", 1, "C", "A"), 0.1),
    (("chr1", 21, "C", "A"), 0.2),
    (("chr1", 31, "C", "A"), 0.3),
])
def test_position_annotator_add_chrom_prefix_tabix_table(
        tmp_path: pathlib.Path, allele: tuple, expected: float) -> None:

    setup_directories(
        tmp_path, {
            "position_score1": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: position_score
                    table:
                        filename: data.txt.gz
                        format: tabix
                        chrom_mapping:
                            add_prefix: chr
                    scores:
                    - id: test100way
                      type: float
                      desc: "test values"
                      name: test100way
                    """),
            }
        })

    setup_tabix(
        tmp_path / "position_score1" / "data.txt.gz",
        """
        #chrom pos_begin pos_end test100way
        1      1         10      0.1
        1      11        20      0.1
        1      21        30      0.2
        1      31        40      0.3
        """, seq_col=0, start_col=1, end_col=2)
    repo = build_filesystem_test_repository(tmp_path)

    pipeline_config = textwrap.dedent("""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  position_aggregator: min
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=repo)
    with pipeline.open() as work_pipeline:
        annotatable = VCFAllele(*allele)
        result = work_pipeline.annotate(annotatable)

        print(annotatable, result)
        assert result.get("test100way") == expected
