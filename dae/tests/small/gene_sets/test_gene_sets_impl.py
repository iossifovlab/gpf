# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pathlib

import pytest
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
def gene_sets_repo(
    grr_contents: dict,
    tmp_path: pathlib.Path,
) -> GenomicResourceRepo:
    root_path = tmp_path
    setup_directories(root_path, grr_contents)
    return build_filesystem_test_repository(root_path)


@pytest.fixture
def gene_sets_impl(
    gene_sets_repo: GenomicResourceRepo,
) -> GeneSetCollectionImpl:
    res = gene_sets_repo.get_resource("test")
    assert res is not None
    return GeneSetCollectionImpl(res)


def test_add_statistics_build_tasks(
    gene_sets_repo: GenomicResourceRepo,
) -> None:

    res = gene_sets_repo.get_resource("test")
    assert res is not None

    gene_sets_collection_impl = GeneSetCollectionImpl(res)
    assert gene_sets_collection_impl is not None

    graph = TaskGraph()
    assert len(graph.tasks) == 0

    gene_sets_collection_impl.add_statistics_build_tasks(graph)
    assert len(graph.tasks) == 1


def test_compute_and_save_statistics(
    gene_sets_impl: GeneSetCollectionImpl,
    tmp_path: pathlib.Path,
) -> None:

    statistics_path = tmp_path / "test" / "statistics"
    assert not statistics_path.exists()

    gene_sets_impl._compute_and_save_all_statistics()

    assert (statistics_path / "gene_sets_per_gene_histogram.json").exists()
    assert (statistics_path / "genes_per_gene_set_histogram.json").exists()
    assert (statistics_path / "gene_collection_count_statistics.json").exists()
    assert (statistics_path / "gene_sets_list_statistics.json").exists()

    result = json.loads((
        statistics_path / "gene_collection_count_statistics.json").read_text())
    assert result == {
        "number_of_gene_sets": 3,
        "number_of_unique_genes": 2,
    }

    result = json.loads((
        statistics_path / "genes_per_gene_set_histogram.json").read_text())
    assert result["values"] == {"1": 2, "2": 1}

    result = json.loads((
        statistics_path / "gene_sets_per_gene_histogram.json").read_text())
    assert result["values"] == {"2": 2}

    result = json.loads((
        statistics_path / "gene_sets_list_statistics.json").read_text())
    assert result == [
        {"name": "test:02", "count": 2, "desc": "test_second"},
        {"name": "test:01", "count": 1, "desc": "test_first"},
        {"name": "test:03", "count": 1, "desc": "test_third"},
    ]
