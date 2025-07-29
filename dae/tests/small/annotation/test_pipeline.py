# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import textwrap

import pytest
import pytest_mock
from dae.annotation.annotatable import Position
from dae.annotation.annotation_factory import (
    AnnotationConfigurationError,
    load_pipeline_from_yaml,
)
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.genomic_context import (
    GenomicContext,
    SimpleGenomicContext,
    get_genomic_context,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.testing import convert_to_tab_separated, setup_directories
from dae.testing.t4c8_import import t4c8_genome


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
    t4c8_genome(root_path / "grr")
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml",
    ))


@pytest.fixture
def context_fixture(
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> GenomicContext:
    conf_dir = str(tmp_path / "conf")
    home_dir = os.environ["HOME"]
    mocker.patch("os.environ", {
        "DAE_DB_DIR": conf_dir,
        "HOME": home_dir,
    })
    test_context = SimpleGenomicContext(
        {},
        ("test_context",),
    )
    mocker.patch(
        "dae.genomic_resources.genomic_context._REGISTERED_CONTEXT_PROVIDERS",
        [])
    mocker.patch(
        "dae.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
        [test_context])
    context = get_genomic_context()
    assert context is not None

    return context


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


def test_annotation_pipeline_context(
    context_fixture: GenomicContext,
    test_grr: GenomicResourceRepo,
) -> None:
    pipeline_config = textwrap.dedent("""
        preamble:
          summary: asdf
          description: lorem ipsum
          input_reference_genome: t4c8_genome
          metadata:
              foo: bar
              subdata:
                  a: b
        annotators:
          - position_score: score_one
    """)

    pipeline = load_pipeline_from_yaml(pipeline_config, test_grr)
    context = pipeline.build_pipeline_genomic_context()

    assert context_fixture.get_genomic_resources_repository() is None
    pipeline_grr = context.get_genomic_resources_repository()
    assert pipeline_grr is not None
    assert pipeline_grr.get_resource("t4c8_genome") is not None

    pipeline_genome = context.get_reference_genome()
    assert pipeline_genome is not None
    assert pipeline_genome.resource_id == "t4c8_genome"
