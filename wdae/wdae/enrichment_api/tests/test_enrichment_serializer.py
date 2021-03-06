import pytest

from dae.enrichment_tool.event_counters import EnrichmentResult


pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


# @pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_serialize(enrichment_serializer):
    serialize = enrichment_serializer.serialize()

    assert len(serialize) == 2
    assert serialize[0]["selector"] == "phenotype 1"
    assert serialize[0]["peopleGroupId"] == "phenotype"
    assert len(serialize[0]["childrenStats"]) == 2
    assert serialize[0]["childrenStats"]["M"] == 1
    assert serialize[0]["childrenStats"]["F"] == 1

    all_serialized = serialize[0]["missense"]["all"]

    assert all_serialized["name"] == "all"
    assert all_serialized["count"] == 2
    assert all_serialized["overlapped"] == 2
    assert all_serialized["expected"] == 2
    assert all_serialized["pvalue"] == 1
    assert all_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert all_serialized["countFilter"]["effectTypes"] == ["Missense"]
    assert all_serialized["countFilter"]["gender"] == [
        "male",
        "female",
        "unspecified",
    ]
    assert all_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["countFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1"
    ]
    assert all_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["countFilter"]["studyTypes"] == ["we"]
    assert all_serialized["countFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert all_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert all_serialized["overlapFilter"]["effectTypes"] == ["Missense"]
    assert all_serialized["overlapFilter"]["gender"] == [
        "male",
        "female",
        "unspecified",
    ]
    assert all_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["overlapFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1"
    ]
    assert all_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["overlapFilter"]["studyTypes"] == ["we"]
    assert all_serialized["overlapFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert all_serialized["overlapFilter"]["geneSymbols"] == {"SAMD11"}

    rec_serialized = serialize[0]["missense"]["rec"]

    assert rec_serialized["name"] == "rec"
    assert rec_serialized["count"] == 1
    assert rec_serialized["overlapped"] == 1
    assert rec_serialized["expected"] == 1
    assert rec_serialized["pvalue"] == 1
    assert rec_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert rec_serialized["countFilter"]["effectTypes"] == ["Missense"]
    assert rec_serialized["countFilter"]["gender"] == ["male", "female"]
    assert rec_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["countFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1"
    ]
    assert rec_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["countFilter"]["studyTypes"] == ["we"]
    assert rec_serialized["countFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert rec_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert rec_serialized["overlapFilter"]["effectTypes"] == ["Missense"]
    assert rec_serialized["overlapFilter"]["gender"] == ["male", "female"]
    assert rec_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["overlapFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1"
    ]
    assert rec_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["overlapFilter"]["studyTypes"] == ["we"]
    assert rec_serialized["overlapFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert rec_serialized["overlapFilter"]["geneSymbols"] == {"SAMD11"}

    male_serialized = serialize[0]["missense"]["male"]

    assert male_serialized["name"] == "male"
    assert male_serialized["count"] == 1
    assert male_serialized["overlapped"] == 1
    assert male_serialized["expected"] == 1
    assert male_serialized["pvalue"] == 1
    assert male_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert male_serialized["countFilter"]["effectTypes"] == ["Missense"]
    assert male_serialized["countFilter"]["gender"] == ["male"]
    assert male_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert male_serialized["countFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1"
    ]
    assert male_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert male_serialized["countFilter"]["studyTypes"] == ["we"]
    assert male_serialized["countFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert male_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert male_serialized["overlapFilter"]["effectTypes"] == ["Missense"]
    assert male_serialized["overlapFilter"]["gender"] == ["male"]
    assert male_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert male_serialized["overlapFilter"]["peopleGroup"][
        "checkedValues"
    ] == ["phenotype1"]
    assert male_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert male_serialized["overlapFilter"]["studyTypes"] == ["we"]
    assert male_serialized["overlapFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert male_serialized["overlapFilter"]["geneSymbols"] == {"SAMD11"}

    female_serialized = serialize[0]["missense"]["female"]

    assert female_serialized["name"] == "female"
    assert female_serialized["count"] == 1
    assert female_serialized["overlapped"] == 1
    assert female_serialized["expected"] == 1
    assert female_serialized["pvalue"] == 1
    assert female_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert female_serialized["countFilter"]["effectTypes"] == ["Missense"]
    assert female_serialized["countFilter"]["gender"] == ["female"]
    assert female_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert female_serialized["countFilter"]["peopleGroup"][
        "checkedValues"
    ] == ["phenotype1"]
    assert female_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert female_serialized["countFilter"]["studyTypes"] == ["we"]
    assert female_serialized["countFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert female_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert female_serialized["overlapFilter"]["effectTypes"] == ["Missense"]
    assert female_serialized["overlapFilter"]["gender"] == ["female"]
    assert (
        female_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    )
    assert female_serialized["overlapFilter"]["peopleGroup"][
        "checkedValues"
    ] == ["phenotype1"]
    assert (
        female_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    )
    assert female_serialized["overlapFilter"]["studyTypes"] == ["we"]
    assert female_serialized["overlapFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
    ]
    assert female_serialized["overlapFilter"]["geneSymbols"] == {"SAMD11"}


def test_serialize_error(f1_trio, enrichment_builder, enrichment_serializer):
    male_er = EnrichmentResult("male")
    male_er.events = [["SAMD11"], ["SAMD11"], ["POGZ"]]
    male_er.overlapped = [["SAMD11"]]
    male_er.expected = 3
    male_er.pvalue = 0.5
    all_er = EnrichmentResult("all")
    all_er.events = [["SAMD11"], ["SAMD11"], ["POGZ"]]
    all_er.overlapped = [["SAMD11"]]
    all_er.expected = 3
    all_er.pvalue = 0.5

    person_set_collection = f1_trio.get_person_set_collection("phenotype")
    with pytest.raises(KeyError):
        enrichment_builder.build_people_group_selector(
            ["missense"],
            person_set_collection.person_sets["autism"]
        )


def test_serialize_enrichment_result(db, enrichment_serializer):
    enrichment_result = EnrichmentResult("all")
    enrichment_result.events = [["SAMD11"], ["SAMD11"], ["POGZ"]]
    enrichment_result.overlapped = [["SAMD11"]]
    enrichment_result.expected = 3
    enrichment_result.pvalue = 0.5

    res = enrichment_serializer.serialize_enrichment_result(enrichment_result)
    assert len(res) == 5
    assert res["name"] == "all"
    assert res["count"] == 3
    assert res["overlapped"] == 1
    assert res["expected"] == 3
    assert res["pvalue"] == 0.5

    with pytest.raises(AssertionError):
        enrichment_serializer.serialize_enrichment_result({})
