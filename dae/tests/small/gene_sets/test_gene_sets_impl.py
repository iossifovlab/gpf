# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pathlib import Path

import pytest
from dae.gene_sets.gene_sets_db import (
    build_gene_set_collection_from_resource_id,
)
from dae.gene_sets.implementations.gene_sets_impl import GeneSetCollectionImpl
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_directories,
)
from dae.task_graph.graph import TaskGraph


@pytest.fixture
def gene_sets_repo_fixture(
    grr_contents,
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, GenomicResourceRepo]:
    root_path = tmp_path_factory.mktemp("gene_sets_repo_tests")
    setup_directories(root_path, grr_contents)
    return root_path, build_filesystem_test_repository(root_path)


@pytest.fixture
def gene_sets_repo_path(  # noqa: FURB118
    gene_sets_repo_fixture,
) -> Path:
    return gene_sets_repo_fixture[0]


def test_add_statistics_build_tasks(
    gene_sets_repo_in_memory: GenomicResourceRepo,
) -> None:
    build_gene_set_collection_from_resource_id("test", gene_sets_repo_in_memory)

    res = gene_sets_repo_in_memory.get_resource("test")
    assert res is not None

    gene_sets_collection_impl = GeneSetCollectionImpl(res)
    assert gene_sets_collection_impl is not None

    graph = TaskGraph()
    assert len(graph.tasks) == 0

    gene_sets_collection_impl.add_statistics_build_tasks(graph)
    assert len(graph.tasks) == 1
