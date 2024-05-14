# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.genomic_resources.implementations.annotation_pipeline_impl import (
    AnnotationPipelineImplementation,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_directories,
)


@pytest.fixture()
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
