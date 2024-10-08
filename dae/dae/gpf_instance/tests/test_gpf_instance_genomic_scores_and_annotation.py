# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import Callable

import pytest

from dae.genomic_resources.repository_factory import (
    build_genomic_resource_group_repository,
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing import (
    setup_directories,
    setup_empty_gene_models,
    setup_genome,
    setup_gpf_instance,
)


@pytest.fixture()
def gpf_fixture(
    fixture_dirname: Callable, tmp_path_factory: pytest.TempPathFactory,
) -> Callable:
    def builder(instance_config: dict) -> GPFInstance:
        root_path = tmp_path_factory.mktemp("genomic_scores_db")
        grr = build_genomic_resource_repository(
            {
                "id": "fixtures",
                "type": "directory",
                "directory": fixture_dirname("genomic_resources"),
            },
        )

        setup_genome(
            root_path / "alla_gpf" / "genome" / "allChr.fa",
            f"""
            >chrA
            {100 * "A"}
            """,
        )
        setup_empty_gene_models(
            root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
        local_repo = build_genomic_resource_repository({
            "id": "alla_local",
            "type": "directory",
            "directory": str(root_path / "alla_gpf"),
        })

        setup_directories(
            root_path / "gpf_instance",
            instance_config,
        )

        return setup_gpf_instance(
            root_path / "gpf_instance",
            reference_genome_id="genome",
            gene_models_id="empty_gene_models",
            grr=build_genomic_resource_group_repository(
                "repo_id", [local_repo, grr]),
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
            - np_score: hg19/MPC
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
            - np_score: hg19/MPC
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
            - np_score: hg19/MPC
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
