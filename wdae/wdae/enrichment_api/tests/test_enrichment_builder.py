import pytest


pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


def test_build(enrichment_builder):
    assert enrichment_builder
    build = enrichment_builder.build()
    print(build)

    assert build
    assert len(build) == 2

    assert sorted([b["peopleGroupValue"] for b in build]) == sorted(
        ["phenotype1", "unaffected"]
    )


# @pytest.mark.xfail(reason='[gene models] wrong annotation')
def test_build_people_group_selector(enrichment_builder, f1_trio):
    assert enrichment_builder
    person_set_collection = f1_trio.get_person_set_collection("phenotype")
    assert person_set_collection is not None
    assert len(person_set_collection.person_sets) == 5

    build = enrichment_builder.build_people_group_selector(
        ["Missense"], person_set_collection, "phenotype1"
    )

    assert build
    assert len(build["childrenStats"]) == 2
    assert build["childrenStats"]["M"] == 1
    assert build["childrenStats"]["F"] == 1
    assert build["selector"] == "phenotype1"
    assert build["geneSymbols"] == ["SAMD11", "PLEKHN1", "POGZ"]
    assert build["peopleGroupId"] == "phenotype"
    assert build["peopleGroupValue"] == "phenotype1"
    assert build["datasetId"] == "f1_trio"
    assert build["Missense"]["all"].expected == 2
    assert build["Missense"]["rec"].expected == 1
    assert build["Missense"]["male"].expected == 1
    assert build["Missense"]["female"].expected == 1
