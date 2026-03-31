# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from gain.annotation.annotation_factory import load_pipeline_from_file
from gain.genomic_resources.repository import GenomicResourceRepo


@pytest.mark.parametrize(
        "pipeline_ext", [".yaml", ".yml"],
)
def test_load_pipeline_from_file(
    annotate_directory_fixture: pathlib.Path,  # noqa: ARG001
    annotation_grr: GenomicResourceRepo,
    tmp_path: pathlib.Path,
    pipeline_ext: str,
) -> None:
    pipeline_filename = tmp_path / f"pipeline{pipeline_ext}"
    pipeline_filename.write_text(
        """
        - position_score:
            resource_id: one
        """)
    pipeline = load_pipeline_from_file(
        str(pipeline_filename), annotation_grr)
    assert len(pipeline.annotators) == 1
