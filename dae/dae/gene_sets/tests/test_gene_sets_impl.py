# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pathlib import Path

import pytest_mock

from dae.gene_sets.gene_sets_db import (
    build_gene_set_collection_from_resource_id,
)
from dae.gene_sets.implementations.gene_sets_impl import GeneSetCollectionImpl
from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
)
from dae.task_graph.graph import TaskGraph


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
    assert len(graph.tasks) == 0


def test_calc_statistics_hash(
    gene_sets_repo_path: Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    calc_statistics_hash_mock = mocker.patch(
        "dae.gene_sets.gene_sets_db.GeneSetCollectionImpl.calc_statistics_hash",
        autospec=True,
    )
    calc_statistics_hash_mock.return_value = b""

    add_statistics_build_tasks_mock = mocker.patch(
        "dae.gene_sets.gene_sets_db.GeneSetCollectionImpl.add_statistics_build_tasks",
        autospec=True,
    )
    add_statistics_build_tasks_mock.return_value = b""

    cli_manage([
        "repo-repair", "-R", str(gene_sets_repo_path), "-j", "1",
    ])

    assert calc_statistics_hash_mock.called is True
    assert add_statistics_build_tasks_mock.called is True
