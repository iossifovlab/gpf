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
