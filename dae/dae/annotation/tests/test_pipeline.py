# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
import pytest
from dae.annotation.annotatable import Position
from dae.annotation.annotation_factory import build_annotation_pipeline, \
    AnnotationConfigurationError
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.testing import setup_directories, convert_to_tab_separated


@pytest.fixture
def test_grr(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path
    setup_directories(
        root_path, {
            "grr.yaml": textwrap.dedent(f"""
                id: reannotation_repo
                type: dir
                directory: "{root_path}/grr"
            """),
            "grr": {
                "score_one": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: s1
                          type: float
                          name: s1
                    """),
                    "data.txt": convert_to_tab_separated("""
                        chrom  pos_begin  s1
                        foo    1          0.1
                    """)
                },
                "score_two": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: s2
                          type: float
                          name: s2
                    """),
                    "data.txt": convert_to_tab_separated("""
                        chrom  pos_begin  s2
                        foo    1          0.2
                    """)
                },
                "dup_score_one": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: s1
                          type: float
                          name: s1
                    """),
                    "data.txt": convert_to_tab_separated("""
                        chrom  pos_begin  s1
                        foo    1          0.123
                    """)
                },
            },
        }
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml"
    ))


def test_build_pipeline(
    annotation_config: str, grr_fixture: GenomicResourceRepo
) -> None:
    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config,
        grr_repository=grr_fixture)

    assert len(pipeline.annotators) == 5


def test_build_pipeline_schema(
    annotation_config: str, grr_fixture: GenomicResourceRepo
) -> None:
    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config,
        grr_repository=grr_fixture)

    attribute = pipeline.get_attribute_info("gene_effects")
    assert attribute is not None
    assert attribute.type == "str", attribute

    attribute = pipeline.get_attribute_info("cadd_raw")
    assert attribute is not None
    assert attribute.type == "float", attribute


def test_pipeline_with_wildcards(test_grr: GenomicResourceRepo) -> None:
    pipeline_config = """
        - position_score: score_*
    """
    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=test_grr)
    result = pipeline.annotate(Position("foo", 1))
    assert len(pipeline.annotators) == 2
    assert result == {"s1": 0.1, "s2": 0.2}


def test_pipeline_repeated_attributes_forbidden(
    test_grr: GenomicResourceRepo
) -> None:
    pipeline_config = """
        - position_score: "*score_one"
    """
    with pytest.raises(AnnotationConfigurationError) as error:
        build_annotation_pipeline(
            pipeline_config_str=pipeline_config,
            grr_repository=test_grr
        )
        assert str(error) == (
            "The annotator repeats the attributes s1"
            " that are already in the pipeline."
        )


def test_pipeline_repeated_attributes_allowed(
    test_grr: GenomicResourceRepo
) -> None:
    pipeline_config = """
        - position_score: "*score_one"
    """
    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=test_grr,
        allow_repeated_attributes=True
    )
    result = pipeline.annotate(Position("foo", 1))
    assert len(pipeline.annotators) == 2
    assert result == {"s1_(#0-score_one)": 0.1, "s1_(#0-dup_score_one)": 0.123}
