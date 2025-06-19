# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.implementations.annotation_pipeline_impl import (
    AnnotationPipelineImplementation,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_directories,
)


@pytest.fixture
def grr_fixture(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path / "grr"
    setup_directories(root_path, {
        "one": {
            "genomic_resource.yaml": """
                type: position_score
                table:
                    filename: data.txt
                scores:
                - id: score
                  type: float
                  desc: |
                      A score description testtest
                  name: s1
            """,
        },
        "pipeline": {
            "genomic_resource.yaml": """
                type: annotation_pipeline
                filename: annotation.yaml
            """,
            "annotation.yaml": """
                - position_score: one
            """,
        },
    })
    return build_filesystem_test_repository(root_path)


@pytest.fixture
def alt_grr_fixture(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path / "alt_grr"
    setup_directories(root_path, {
        "other_score": {
            "genomic_resource.yaml": """
                type: position_score
                table:
                    filename: data.txt
                scores:
                - id: score
                  type: float
                  name: s1
            """,
        },
    })
    return build_filesystem_test_repository(root_path)


def test_pipeline_impl_init(grr_fixture: GenomicResourceRepo) -> None:
    assert AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"))


def test_pipeline_impl_info(grr_fixture: GenomicResourceRepo) -> None:
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"))
    info = impl.get_info(repo=grr_fixture)
    assert info
    assert "position_score" in info
    assert "one" in info
    assert "A score description testtest" in info


def test_pipeline_doc_resource_url(
    grr_fixture: GenomicResourceRepo,
    alt_grr_fixture: GenomicResourceRepo,
) -> None:
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"))

    res = grr_fixture.get_resource("one")
    other_res = alt_grr_fixture.get_resource("other_score")

    assert impl._make_resource_url(res) == "../one"
    assert impl._make_resource_url(other_res) == other_res.get_url()


def test_pipeline_doc_histogram_url(
    grr_fixture: GenomicResourceRepo,
    alt_grr_fixture: GenomicResourceRepo,
) -> None:
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"))

    score = build_score_from_resource(
        grr_fixture.get_resource("one"))
    other_score = build_score_from_resource(
        alt_grr_fixture.get_resource("other_score"))

    assert impl._make_histogram_url(score, "s1") \
        == "../one/statistics/histogram_s1.png"
    assert impl._make_histogram_url(other_score, "s1") == \
        other_score.get_histogram_image_url("s1")
