# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.gene.gene_sets_db import GeneSetCollection, GeneSetsDb
from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.fixture
def gene_sets_repo(tmp_path):
    sets_repo = build_inmemory_test_repository({
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
                )
            }
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
            )
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
            )
        }
    })
    return sets_repo


@pytest.fixture
def gene_sets_db(gene_sets_repo):
    resources = [
        gene_sets_repo.get_resource("main"),
        gene_sets_repo.get_resource("test_mapping"),
        gene_sets_repo.get_resource("test_gmt"),
    ]
    gene_set_collections = [
        GeneSetCollection(r) for r in resources
    ]
    return GeneSetsDb(gene_set_collections)


def test_gene_set_collection_main(gene_sets_repo):
    resource = gene_sets_repo.get_resource("main")
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


def test_get_gene_set_collection_ids(gene_sets_db):
    assert gene_sets_db.get_gene_set_collection_ids() == {
        "main",
        "test_mapping",
        "test_gmt"
    }


def test_get_gene_set_ids(gene_sets_db):
    assert gene_sets_db.get_gene_set_ids("main") == {"main_candidates"}


def test_get_collections_descriptions(gene_sets_db):
    assert gene_sets_db.collections_descriptions == [
        {
            "desc": "Main",
            "name": "main",
            "format": ["key", " (", "count", "): ", "desc"],
            "types": [],
        },
        {
            "desc": "Test mapping",
            "name": "test_mapping",
            "format": ["key", " (", "count", ")"],
            "types": [],
        },
        {
            "desc": "Test GMT",
            "name": "test_gmt",
            "format": ["key", " (", "count", ")"],
            "types": [],
        },
    ]


def test_has_gene_set_collection(gene_sets_db):
    assert gene_sets_db.has_gene_set_collection("main")
    assert gene_sets_db.has_gene_set_collection("test_mapping")
    assert gene_sets_db.has_gene_set_collection("test_gmt")
    assert not gene_sets_db.has_gene_set_collection("nonexistent_gsc")


def test_get_all_gene_sets(gene_sets_db):
    gene_sets = gene_sets_db.get_all_gene_sets("main")

    assert len(gene_sets) == 1
    gene_set = gene_sets[0]

    assert gene_set is not None
    assert gene_set["name"] == "main_candidates"
    assert gene_set["count"] == 9
    assert gene_set["desc"] == "Main Candidates"


def test_get_all_gene_sets_gmt(gene_sets_db):
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


def test_get_all_gene_sets_mapping(gene_sets_db):
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


def test_get_gene_set(gene_sets_db):
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


def test_get_gene_set_gmt(gene_sets_db):
    gene_set = gene_sets_db.get_gene_set("test_gmt", "TEST_GENE_SET1")
    assert gene_set["name"] == "TEST_GENE_SET1"
    assert gene_set["count"] == 2
    assert gene_set["desc"] == "somedescription"
    assert set(gene_set["syms"]) == {"POGZ", "CHD8"}


def test_get_gene_set_mapping(gene_sets_db):
    gene_set = gene_sets_db.get_gene_set("test_mapping", "test:01")
    assert gene_set["name"] == "test:01"
    assert gene_set["count"] == 1
    assert gene_set["desc"] == "test_first"
    assert set(gene_set["syms"]) == {"POGZ"}
