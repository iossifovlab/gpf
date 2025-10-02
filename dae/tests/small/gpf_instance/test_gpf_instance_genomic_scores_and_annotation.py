# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from collections.abc import Callable

import pytest
from dae.genomic_resources.testing import (
    setup_directories,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing.setup_helpers import setup_gpf_instance


@pytest.fixture
def gpf_fixture(
    t4c8_grr, tmp_path_factory: pytest.TempPathFactory,
) -> Callable:
    def builder(instance_config: dict) -> GPFInstance:
        root_path = tmp_path_factory.mktemp("genomic_scores_db")
        setup_directories(
            root_path / "gpf_instance",
            instance_config,
        )
        return setup_gpf_instance(
            root_path / "gpf_instance",
            reference_genome_id="t4c8_genome",
            gene_models_id="t4c8_genes",
            grr=t4c8_grr,
        )

    return builder


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
