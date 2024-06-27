# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
import pytest_mock

import dae.annotation.annotation_factory
from dae.annotation.annotatable import Position
from dae.annotation.annotation_factory import (
    AnnotationConfigurationError,
    load_pipeline_from_file,
    load_pipeline_from_yaml,
    copy_annotation_pipeline,
    copy_reannotation_pipeline,
)
from dae.annotation.annotation_pipeline import ReannotationPipeline
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.testing import convert_to_tab_separated, setup_directories


@pytest.fixture()
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
                    """),
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
                    """),
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
                    """),
                },
            },
        },
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml",
    ))


def test_build_pipeline(
    annotation_config: str, grr_fixture: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_file(annotation_config, grr_fixture)

    assert len(pipeline.annotators) == 5


def test_build_pipeline_schema(
    annotation_config: str, grr_fixture: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_file(annotation_config, grr_fixture)

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
    pipeline = load_pipeline_from_yaml(pipeline_config, test_grr)
    result = pipeline.annotate(Position("foo", 1))
    assert len(pipeline.annotators) == 2
    assert result == {"s1": 0.1, "s2": 0.2}


def test_pipeline_repeated_attributes_forbidden(
    test_grr: GenomicResourceRepo,
) -> None:
    pipeline_config = """
        - position_score: "*score_one"
    """
    with pytest.raises(AnnotationConfigurationError) as error:
        load_pipeline_from_yaml(pipeline_config, test_grr)
    assert str(error.value) == (
        "Repeated attributes in pipeline were found -"
        " {'s1': ['A0_score_one', 'A0_dup_score_one']}"
    )


def test_pipeline_repeated_attributes_allowed(
    test_grr: GenomicResourceRepo,
) -> None:
    pipeline_config = """
        - position_score: "*score_one"
    """
    pipeline = load_pipeline_from_yaml(
        pipeline_config, test_grr,
        allow_repeated_attributes=True,
    )
    result = pipeline.annotate(Position("foo", 1))
    assert len(pipeline.annotators) == 2
    assert result == {"s1_A0_score_one": 0.1, "s1_A0_dup_score_one": 0.123}


def test_copy_pipeline(test_grr: GenomicResourceRepo) -> None:
    pipeline_config = """
        - position_score: score_one
        - position_score: score_two
    """
    pipeline = load_pipeline_from_yaml(pipeline_config, test_grr)
    copied_pipeline = copy_annotation_pipeline(pipeline)

    assert len(pipeline.annotators) == 2
    assert len(copied_pipeline.annotators) == 2

    # pylint: disable=C0200
    for idx in range(len(copied_pipeline.annotators)):
        info_src = pipeline.annotators[idx].get_info()
        info_copy = copied_pipeline.annotators[idx].get_info()
        assert info_copy == info_src
        assert id(info_copy) != id(info_src)


def test_copy_reannotation_pipeline(
    mocker: pytest_mock.MockerFixture,
    test_grr: GenomicResourceRepo,
) -> None:
    pipeline_config_a = """
        - position_score: score_one
    """
    pipeline_config_b = """
        - position_score: score_one
        - position_score: score_two
    """
    pipeline_a = load_pipeline_from_yaml(pipeline_config_a, test_grr)
    pipeline_b = load_pipeline_from_yaml(pipeline_config_b, test_grr)

    reannotation = ReannotationPipeline(
        pipeline_a, pipeline_b)

    mocker.spy(ReannotationPipeline, "__init__")
    mocker.spy(dae.annotation.annotation_factory, "copy_annotation_pipeline")
    copy_method = dae.annotation.annotation_factory.copy_annotation_pipeline

    copied_pipeline = copy_reannotation_pipeline(reannotation)

    assert ReannotationPipeline.__init__.call_count == 1  # type: ignore
    assert copy_method.call_count == 2  # type: ignore
    copy_method.assert_any_call(pipeline_a)  # type: ignore
    copy_method.assert_any_call(pipeline_b)  # type: ignore

    assert len(copied_pipeline.annotators) == len(reannotation.annotators)
