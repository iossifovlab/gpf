# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from pathlib import Path
from typing import Any

import pytest
import pytest_mock

from dae.gene_sets.gene_sets_db import (
    GeneSetCollection,
    GeneSetCollectionImpl,
    GeneSetsDb,
    build_gene_set_collection_from_resource_id,
)
from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    build_inmemory_test_repository,
    convert_to_tab_separated,
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


@pytest.fixture
def gene_sets_repo_in_memory(grr_contents) -> GenomicResourceRepo:
    return build_inmemory_test_repository(grr_contents)


@pytest.fixture
def grr_contents() -> dict[str, Any]:
    return {
        "main": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: main
                format: directory
                directory: GeneSets
                web_label: Main
                web_format_str: "key| (|count|): |desc"
                """),
            "GeneSets": {
                "main_candidates.txt": (
                    "main_candidates\n"
                    "Main Candidates\n"
                    "POGZ\n"
                    "CHD8\n"
                    "ANK2\n"
                    "FAT4\n"
                    "NBEA\n"
                    "CELSR1\n"
                    "USP7\n"
                    "GOLGA5\n"
                    "PCSK2\n"
                ),
                "alt_candidates.txt": (
                    "alt_candidates\n"
                    "Alt Candidates\n"
                    "DIABLO\n"
                ),
            },
        },
        "test_mapping": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: test_mapping
                format: map
                filename: test-map.txt
                web_label: Test mapping
                web_format_str: "key| (|count|)"
            """),
            "test-map.txt": (
                "#geneNS\tsym\n"
                "POGZ\ttest:01 test:02\n"
                "CHD8\ttest:02 test:03\n"
            ),
            "test-mapnames.txt": (
                "test:01\ttest_first\n"
                "test:02\ttest_second\n"
                "test:03\ttest_third\n"
            ),
        },
        "test_gmt": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: test_gmt
                format: gmt
                filename: test-gmt.gmt
                web_label: Test GMT
                web_format_str: "key| (|count|)"
            """),
            "test-gmt.gmt": (
                "TEST_GENE_SET1\tsomedescription\tPOGZ\tCHD8\n"
                "TEST_GENE_SET2\tsomedescription\tANK2\tFAT4\n"
                "TEST_GENE_SET3\tsomedescription\tPOGZ\n"
            ),
        },
        "test": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: test_mapping
                format: map
                filename: test-map.txt
                web_label: Test mapping
                web_format_str: "key| (|count|)"
            """),
            "test-map.txt": convert_to_tab_separated("""
                #geneNS tsym
                POGZ    test:01||test:02
                CHD8    test:02||test:03
            """),
            "test-mapnames.txt": convert_to_tab_separated("""
                test:01  test_first
                test:02  test_second
                test:03  test_third
            """),
        },
    }


@pytest.fixture
def gene_sets_db(
    gene_sets_repo_in_memory: GenomicResourceRepo,
) -> GeneSetsDb:
    resources = [
        gene_sets_repo_in_memory.get_resource("main"),
        gene_sets_repo_in_memory.get_resource("test_mapping"),
        gene_sets_repo_in_memory.get_resource("test_gmt"),
    ]
    gene_set_collections = [
        GeneSetCollection(r) for r in resources
    ]
    return GeneSetsDb(gene_set_collections)


def test_gene_set_collection_main(
    gene_sets_repo_in_memory: GenomicResourceRepo,
) -> None:
    resource = gene_sets_repo_in_memory.get_resource("main")
    gsc = GeneSetCollection(resource)
    gene_set = gsc.get_gene_set("main_candidates")
    assert gene_set is not None
    assert gene_set["name"] == "main_candidates"
    assert gene_set["count"] == 9
    assert set(gene_set["syms"]) == {
        "POGZ",
        "CHD8",
        "ANK2",
        "FAT4",
        "NBEA",
        "CELSR1",
        "USP7",
        "GOLGA5",
        "PCSK2",
    }
    assert gene_set["desc"] == "Main Candidates"


def test_get_gene_set_collection_ids(gene_sets_db: GeneSetsDb) -> None:
    assert gene_sets_db.get_gene_set_collection_ids() == {
        "main",
        "test_mapping",
        "test_gmt",
    }


def test_get_gene_set_ids(gene_sets_db: GeneSetsDb) -> None:
    assert gene_sets_db.get_gene_set_ids("main") == {
        "main_candidates",
         "alt_candidates",
    }


def test_get_collections_descriptions(gene_sets_db: GeneSetsDb) -> None:
    assert gene_sets_db.collections_descriptions == [
        {
            "desc": "Main",
            "name": "main",
            "format": ["key", " (", "count", "): ", "desc"],
        },
        {
            "desc": "Test mapping",
            "name": "test_mapping",
            "format": ["key", " (", "count", ")"],
        },
        {
            "desc": "Test GMT",
            "name": "test_gmt",
            "format": ["key", " (", "count", ")"],
        },
    ]


def test_has_gene_set_collection(gene_sets_db: GeneSetsDb) -> None:
    assert gene_sets_db.has_gene_set_collection("main")
    assert gene_sets_db.has_gene_set_collection("test_mapping")
    assert gene_sets_db.has_gene_set_collection("test_gmt")
    assert not gene_sets_db.has_gene_set_collection("nonexistent_gsc")


def test_get_all_gene_sets(gene_sets_db: GeneSetsDb) -> None:
    gene_sets = gene_sets_db.get_all_gene_sets("main")

    assert len(gene_sets) == 2

    alt_gene_set = gene_sets[0]

    assert alt_gene_set is not None
    assert alt_gene_set["name"] == "alt_candidates"
    assert alt_gene_set["count"] == 1
    assert alt_gene_set["desc"] == "Alt Candidates"

    main_gene_set = gene_sets[1]

    assert main_gene_set is not None
    assert main_gene_set["name"] == "main_candidates"
    assert main_gene_set["count"] == 9
    assert main_gene_set["desc"] == "Main Candidates"


def test_get_all_gene_sets_gmt(gene_sets_db: GeneSetsDb) -> None:
    gene_sets = gene_sets_db.get_all_gene_sets("test_gmt")

    assert len(gene_sets) == 3

    assert gene_sets[0] is not None
    assert gene_sets[0]["name"] == "TEST_GENE_SET1"
    assert gene_sets[0]["count"] == 2
    assert gene_sets[0]["desc"] == "somedescription"

    assert gene_sets[1] is not None
    assert gene_sets[1]["name"] == "TEST_GENE_SET2"
    assert gene_sets[1]["count"] == 2
    assert gene_sets[1]["desc"] == "somedescription"

    assert gene_sets[2] is not None
    assert gene_sets[2]["name"] == "TEST_GENE_SET3"
    assert gene_sets[2]["count"] == 1
    assert gene_sets[2]["desc"] == "somedescription"


def test_get_all_gene_sets_mapping(gene_sets_db: GeneSetsDb) -> None:
    gene_sets = gene_sets_db.get_all_gene_sets("test_mapping")

    assert len(gene_sets) == 3

    assert gene_sets[0] is not None
    assert gene_sets[0]["name"] == "test:01"
    assert gene_sets[0]["count"] == 1
    assert gene_sets[0]["desc"] == "test_first"

    assert gene_sets[1] is not None
    assert gene_sets[1]["name"] == "test:02"
    assert gene_sets[1]["count"] == 2
    assert gene_sets[1]["desc"] == "test_second"

    assert gene_sets[2] is not None
    assert gene_sets[2]["name"] == "test:03"
    assert gene_sets[2]["count"] == 1
    assert gene_sets[2]["desc"] == "test_third"


def test_get_gene_set(gene_sets_db: GeneSetsDb) -> None:
    gene_set = gene_sets_db.get_gene_set("main", "main_candidates")

    assert gene_set is not None
    assert gene_set["name"] == "main_candidates"
    assert gene_set["count"] == 9
    assert set(gene_set["syms"]) == {
        "POGZ",
        "CHD8",
        "ANK2",
        "FAT4",
        "NBEA",
        "CELSR1",
        "USP7",
        "GOLGA5",
        "PCSK2",
    }
    assert gene_set["desc"] == "Main Candidates"


def test_get_gene_set_gmt(gene_sets_db: GeneSetsDb) -> None:
    gene_set = gene_sets_db.get_gene_set("test_gmt", "TEST_GENE_SET1")
    assert gene_set is not None
    assert gene_set["name"] == "TEST_GENE_SET1"
    assert gene_set["count"] == 2
    assert gene_set["desc"] == "somedescription"
    assert set(gene_set["syms"]) == {"POGZ", "CHD8"}


def test_get_gene_set_mapping(gene_sets_db: GeneSetsDb) -> None:
    gene_set = gene_sets_db.get_gene_set("test_mapping", "test:01")
    assert gene_set is not None
    assert gene_set["name"] == "test:01"
    assert gene_set["count"] == 1
    assert gene_set["desc"] == "test_first"
    assert set(gene_set["syms"]) == {"POGZ"}


def test_get_gene_set_collection_files(gene_sets_db: GeneSetsDb) -> None:
    """Get a collection list of files"""
    gene_set_collections = gene_sets_db.gene_set_collections

    assert gene_set_collections["main"].files == {
        "GeneSets/main_candidates.txt",
        "GeneSets/alt_candidates.txt",
    }

    assert gene_set_collections["test_mapping"].files == {
        "test-map.txt",
        "test-mapnames.txt",
    }

    assert gene_set_collections["test_gmt"].files == {
        "test-gmt.gmt",
    }


def test_build_gene_set_collection_from_resource_id(
    gene_sets_repo_in_memory: GenomicResourceRepo,
) -> None:
    gsc = build_gene_set_collection_from_resource_id(
        "main",
        gene_sets_repo_in_memory,
    )
    gene_set = gsc.get_gene_set("main_candidates")
    assert gene_set is not None
    assert gene_set["name"] == "main_candidates"
    assert gene_set["count"] == 9
    assert set(gene_set["syms"]) == {
        "POGZ",
        "CHD8",
        "ANK2",
        "FAT4",
        "NBEA",
        "CELSR1",
        "USP7",
        "GOLGA5",
        "PCSK2",
    }
    assert gene_set["desc"] == "Main Candidates"


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
        "repo-repair", "-R", str(gene_sets_repo_path), "-j", "1", "--no-cache",
    ])

    assert calc_statistics_hash_mock.called is True
    assert add_statistics_build_tasks_mock.called is True
