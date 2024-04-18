# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.enrichment_tool.event_counters import EnrichmentSingleResult
from enrichment_api.enrichment_serializer import EnrichmentSerializer

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_serialize(enrichment_serializer: EnrichmentSerializer) -> None:
    # pylint: disable=too-many-statements
    serialize = enrichment_serializer.serialize()

    assert len(serialize) == 2
    assert serialize[0]["selector"] == "phenotype 1"
    assert serialize[0]["peopleGroupId"] == "phenotype"
    assert len(serialize[0]["childrenStats"]) == 3
    assert serialize[0]["childrenStats"]["M"] == 1
    assert serialize[0]["childrenStats"]["F"] == 1
    assert serialize[0]["childrenStats"]["U"] == 0

    all_serialized = serialize[0]["missense"]["all"]

    assert all_serialized["name"] == "all"
    assert all_serialized["count"] == 2
    assert all_serialized["overlapped"] == 2
    assert all_serialized["expected"] == 2
    assert all_serialized["pvalue"] == 1
    assert all_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert all_serialized["countFilter"]["effectTypes"] == ["missense"]
    assert all_serialized["countFilter"]["gender"] == [
        "male",
        "female",
        "unspecified",
    ]
    assert all_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["countFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1",
    ]
    assert all_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["countFilter"]["studyTypes"] == ["we"]
    assert all_serialized["countFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
        "complex",
    ]
    assert all_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert all_serialized["overlapFilter"]["effectTypes"] == ["missense"]
    assert all_serialized["overlapFilter"]["gender"] == [
        "male",
        "female",
        "unspecified",
    ]
    assert all_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["overlapFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1",
    ]
    assert all_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert all_serialized["overlapFilter"]["studyTypes"] == ["we"]
    assert all_serialized["overlapFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
        "complex",
    ]
    # assert all_serialized["overlapFilter"]["geneSymbols"] == {"SAMD11"}

    rec_serialized = serialize[0]["missense"]["rec"]

    assert rec_serialized["name"] == "rec"
    assert rec_serialized["count"] == 1
    assert rec_serialized["overlapped"] == 1
    assert rec_serialized["expected"] == 1
    assert rec_serialized["pvalue"] == 1
    assert rec_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert rec_serialized["countFilter"]["effectTypes"] == ["missense"]
    assert rec_serialized["countFilter"]["gender"] == [
        "male", "female", "unspecified"]
    assert rec_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["countFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1",
    ]
    assert rec_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["countFilter"]["studyTypes"] == ["we"]
    assert rec_serialized["countFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
        "complex",
    ]
    assert rec_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert rec_serialized["overlapFilter"]["effectTypes"] == ["missense"]
    assert rec_serialized["overlapFilter"]["gender"] == \
        ["male", "female", "unspecified"]
    assert rec_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["overlapFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1",
    ]
    assert rec_serialized["overlapFilter"]["peopleGroup"]["id"] == "phenotype"
    assert rec_serialized["overlapFilter"]["studyTypes"] == ["we"]
    assert rec_serialized["overlapFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
        "complex",
    ]
    assert rec_serialized["overlapFilter"]["overlappedGenes"] == {"SAMD11"}

    male_serialized = serialize[0]["missense"]["male"]

    assert male_serialized["name"] == "male"
    assert male_serialized["count"] == 1
    assert male_serialized["overlapped"] == 1
    assert male_serialized["expected"] == 1
    assert male_serialized["pvalue"] == 1
    assert male_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert male_serialized["countFilter"]["effectTypes"] == ["missense"]
    assert male_serialized["countFilter"]["gender"] == ["male"]
    assert male_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert male_serialized["countFilter"]["peopleGroup"]["checkedValues"] == [
        "phenotype1",
    ]
    assert male_serialized["countFilter"]["peopleGroup"]["id"] == "phenotype"
    assert male_serialized["countFilter"]["studyTypes"] == ["we"]
    assert male_serialized["countFilter"]["variantTypes"] == [
        "ins",
        "sub",
        "del",
        "complex",
    ]
    assert male_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert male_serialized["overlapFilter"]["effectTypes"] == ["missense"]
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
        "complex",
    ]
    # assert male_serialized["overlapFilter"]["geneSymbols"] == {"SAMD11"}

    female_serialized = serialize[0]["missense"]["female"]

    assert female_serialized["name"] == "female"
    assert female_serialized["count"] == 1
    assert female_serialized["overlapped"] == 1
    assert female_serialized["expected"] == 1
    assert female_serialized["pvalue"] == 1
    assert female_serialized["countFilter"]["datasetId"] == "f1_trio"
    assert female_serialized["countFilter"]["effectTypes"] == ["missense"]
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
        "complex",
    ]
    assert female_serialized["overlapFilter"]["datasetId"] == "f1_trio"
    assert female_serialized["overlapFilter"]["effectTypes"] == ["missense"]
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
        "complex",
    ]
    # assert female_serialized["overlapFilter"]["geneSymbols"] == {"SAMD11"}


def test_serialize_enrichment_result(
    enrichment_serializer: EnrichmentSerializer,
) -> None:
    enrichment_result = EnrichmentSingleResult(
        "all",
        3,
        1,
        3,
        0.5,
    )

    res = enrichment_serializer.serialize_enrichment_result(enrichment_result)
    assert len(res) == 5
    assert res["name"] == "all"
    assert res["count"] == 3
    assert res["overlapped"] == 1
    assert res["expected"] == 3
    assert res["pvalue"] == 0.5
