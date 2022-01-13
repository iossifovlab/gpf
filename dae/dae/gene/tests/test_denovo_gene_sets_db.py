import pytest


pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")


def name_in_gene_sets(gene_sets, name, count=None):
    for gene_set in gene_sets:
        if gene_set["name"] == name:
            print(gene_set)
            if count is not None:
                if gene_set["count"] == count:
                    return True
                else:
                    return False
            return True

    return False


def test_get_all_descriptions(denovo_gene_sets_db):
    gene_set_descriptions = denovo_gene_sets_db.get_gene_set_descriptions()

    assert gene_set_descriptions["desc"] == "Denovo"
    assert gene_set_descriptions["name"] == "denovo"
    assert gene_set_descriptions["format"] == ["key", " (|count|)"]
    assert len(gene_set_descriptions["types"]) == 4


def test_get_f4_descriptions(denovo_gene_sets_db):
    gene_set_descriptions = denovo_gene_sets_db.get_gene_set_descriptions(
        permitted_datasets=["f4_trio"]
    )

    assert gene_set_descriptions["desc"] == "Denovo"
    assert gene_set_descriptions["name"] == "denovo"
    assert gene_set_descriptions["format"] == ["key", " (|count|)"]
    assert len(gene_set_descriptions["types"]) == 1
    assert gene_set_descriptions["types"][0]["datasetId"] == "f4_trio"
    assert gene_set_descriptions["types"][0]["datasetName"] == "f4_trio"
    assert gene_set_descriptions["types"][0]["personSetCollectionId"] == \
        "phenotype"
    assert gene_set_descriptions["types"][0]["personSetCollectionName"] == \
        "Phenotype"
    assert len(
        gene_set_descriptions["types"][0]["personSetCollectionLegend"]) == 2


@pytest.mark.parametrize(
    "denovo_gene_set_id,people_groups,count",
    [
        ("Missense", ["autism"], 1),
        ("Missense", ["autism", "unaffected"], 1),
        ("Synonymous", ["autism"], 1),
        ("Synonymous", ["unaffected"], 1),
        ("Synonymous", ["autism", "unaffected"], 2),
    ],
)
def test_get_denovo_gene_set_f4(
    denovo_gene_sets_db, denovo_gene_set_id, people_groups, count
):
    dgs = denovo_gene_sets_db.get_gene_set(
        denovo_gene_set_id, {"f4_trio": {"phenotype": people_groups}}
    )

    assert dgs is not None
    assert dgs["count"] == count
    assert dgs["name"] == denovo_gene_set_id
    assert dgs["desc"] == "{} (f4_trio:phenotype:{})".format(
        denovo_gene_set_id, ",".join(people_groups)
    )


@pytest.mark.parametrize(
    "denovo_gene_set_id,people_groups",
    [
        ("LGDs", ["autism"]),
        ("LGDs", ["unaffected"]),
        ("LGDs", ["autism", "unaffected"]),
        ("Missense", ["unaffected"]),
    ],
)
def test_get_denovo_gene_set_f4_empty(
    denovo_gene_sets_db, denovo_gene_set_id, people_groups
):
    dgs = denovo_gene_sets_db.get_gene_set(
        denovo_gene_set_id, {"f4_trio": {"phenotype": people_groups}}
    )

    assert dgs is None


def test_get_denovo_gene_sets_f4_autism(denovo_gene_sets_db):
    dgs = denovo_gene_sets_db.get_all_gene_sets(
        {"f4_trio": {"phenotype": ["autism"]}}
    )

    assert dgs is not None
    assert len(dgs) == 4
    assert name_in_gene_sets(dgs, "Synonymous", 1)
    assert name_in_gene_sets(dgs, "Missense", 1)
    assert name_in_gene_sets(dgs, "Missense.Recurrent", 1)
    assert name_in_gene_sets(dgs, "Missense.Female", 1)


def test_get_denovo_gene_sets_f4_unaffected(denovo_gene_sets_db):
    dgs = denovo_gene_sets_db.get_all_gene_sets(
        {"f4_trio": {"phenotype": ["unaffected"]}}
    )

    assert dgs is not None
    assert len(dgs) == 1
    assert name_in_gene_sets(dgs, "Synonymous", 1)


def test_get_denovo_gene_sets_f4_autism_unaffected(denovo_gene_sets_db):
    dgs = denovo_gene_sets_db.get_all_gene_sets(
        {"f4_trio": {"phenotype": ["autism", "unaffected"]}}
    )

    assert dgs is not None
    assert len(dgs) == 4
    assert name_in_gene_sets(dgs, "Synonymous", 2)
    assert name_in_gene_sets(dgs, "Missense", 1)
    assert name_in_gene_sets(dgs, "Missense.Recurrent", 1)
    assert name_in_gene_sets(dgs, "Missense.Female", 1)


def test_all_denovo_gene_set_ids(denovo_gene_sets_db):
    assert sorted(denovo_gene_sets_db.get_genotype_data_ids()) == sorted(
        ["f1_group", "f2_group", "f3_group", "f4_trio"]
    )
