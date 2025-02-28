# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.gene_sets.gene_sets_db import (
    GeneSetCollection,
    GeneSetsDb,
    build_gene_set_collection_from_resource_id,
)
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
)


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
