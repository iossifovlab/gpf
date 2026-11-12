# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import tempfile
import textwrap
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from gain.genomic_resources.repository import GenomicResourceRepo
from gain.genomic_resources.testing import (
    setup_directories,
)

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.testing.setup_helpers import setup_gpf_instance


@pytest.fixture
def gpf_fixture(
    t4c8_grr: GenomicResourceRepo,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[Callable, None, None]:
    instances: list[GPFInstance] = []

    def builder(instance_config: dict) -> GPFInstance:
        root_path = tmp_path_factory.mktemp("genomic_scores_db")
        setup_directories(
            root_path / "gpf_instance",
            instance_config,
        )
        instance = setup_gpf_instance(
            root_path / "gpf_instance",
            reference_genome_id="t4c8_genome",
            gene_models_id="t4c8_genes",
            grr=t4c8_grr,
        )
        instances.append(instance)
        return instance

    yield builder
    for instance in instances:
        instance.shutdown()


def test_genomic_scores_db_with_config(gpf_fixture: Callable) -> None:
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            instance_id: test_instance
            annotation:
              conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
            - position_score: genomic_scores/score_one
        """),
    })
    assert len(gpf_instance.genomic_scores) == 1


def test_genomic_scores_db_without_config_with_annotation(
    gpf_fixture: Callable,
) -> None:
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            instance_id: test_instance
            annotation:
              conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
            - position_score: genomic_scores/score_one
        """),
    })
    assert len(gpf_instance.genomic_scores) == 1


def test_genomic_scores_db_without_config_without_annotation(
    gpf_fixture: Callable,
) -> None:
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            instance_id: test_instance
        """),
    })
    assert len(gpf_instance.genomic_scores) == 0


def test_annotation_pipeline_with_config(gpf_fixture: Callable) -> None:
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            instance_id: test_instance
            annotation:
              conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
            - position_score: genomic_scores/score_one
        """),
    })
    assert gpf_instance.get_annotation_pipeline() is not None
    assert len(gpf_instance.get_annotation_pipeline().annotators) == 2


def test_annotation_pipeline_without_config(gpf_fixture: Callable) -> None:
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            instance_id: test_instance
        """),
    })
    assert gpf_instance.get_annotation_pipeline() is not None
    assert len(gpf_instance.get_annotation_pipeline().annotators) == 1


def test_annotation_pipeline_with_bad_config(gpf_fixture: Callable) -> None:
    gpf_instance = gpf_fixture({
        "gpf_instance.yaml": textwrap.dedent("""
            instance_id: test_instance
            annotation:
              conf_file: annotation.yaml
        """),
    })
    with pytest.raises(
            ValueError,
            match="annotation config file not found"):
        gpf_instance.get_annotation_pipeline()


_ANNOTATION_INSTANCE_CONFIG = {
    "gpf_instance.yaml": textwrap.dedent("""
        instance_id: test_instance
        annotation:
          conf_file: annotation.yaml
    """),
    "annotation.yaml": textwrap.dedent("""
        - position_score: genomic_scores/score_one
    """),
}


def _annotation_work_dir_parents(gpf_instance: GPFInstance) -> set[Path]:
    pipeline = gpf_instance.get_annotation_pipeline()
    return {
        Path(annotator.work_dir).parent
        for annotator in pipeline.annotators
    }


def test_annotation_pipeline_gets_an_explicit_temp_work_dir(
    gpf_fixture: Callable,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    first = gpf_fixture(_ANNOTATION_INSTANCE_CONFIG)
    second = gpf_fixture(_ANNOTATION_INSTANCE_CONFIG)

    with caplog.at_level(logging.WARNING):
        first_parents = _annotation_work_dir_parents(first)
        first_again_parents = _annotation_work_dir_parents(first)
        second_parents = _annotation_work_dir_parents(second)

    assert not [
        record for record in caplog.records
        if record.name == "gain.annotation.annotation_factory"
        and "no `work_dir` passed" in record.getMessage()
    ]
    assert len(first_parents) == 1
    first_parent = first_parents.pop()
    assert first_parent.parent == tmp_path
    assert first_parent.name.startswith("gpf-annotation-")
    assert first_again_parents == {first_parent}
    assert len(second_parents) == 1
    assert second_parents.pop() != first_parent
