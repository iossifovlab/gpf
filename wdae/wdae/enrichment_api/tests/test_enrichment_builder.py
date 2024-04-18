# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.studies.study import GenotypeData
from enrichment_api.enrichment_builder import EnrichmentBuilder

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_build_results(enrichment_builder: EnrichmentBuilder) -> None:
    assert enrichment_builder
    build = enrichment_builder.build_results()
    print(build)

    assert build
    assert len(build) == 2

    assert sorted([b["peopleGroupValue"] for b in build]) == sorted(
        ["phenotype1", "unaffected"],
    )


def test_build(enrichment_builder: EnrichmentBuilder) -> None:
    assert enrichment_builder
    build = enrichment_builder.build_results()
    print(build)

    assert build
    assert len(build) == 2

    assert sorted([b["selector"] for b in build]) == sorted(
        ["phenotype 1", "unaffected"],
    )


def test_build_people_group_selector(
    enrichment_builder: EnrichmentBuilder,
    f1_trio: GenotypeData,
) -> None:
    assert enrichment_builder
    person_set_collection = f1_trio.get_person_set_collection("phenotype")
    assert person_set_collection is not None
    assert len(person_set_collection.person_sets) == 2

    results = enrichment_builder.build_results()

    build = None
    for build in results:
        if build["peopleGroupValue"] == "phenotype1":
            break

    assert build is not None
    assert len(build["childrenStats"]) == 3
    assert build["childrenStats"]["M"] == 1
    assert build["childrenStats"]["F"] == 1
    assert build["childrenStats"]["U"] == 0
    assert build["selector"] == "phenotype 1"
    assert build["geneSymbols"] == ["SAMD11", "PLEKHN1", "POGZ"]
    assert build["peopleGroupId"] == "phenotype"
    assert build["peopleGroupValue"] == "phenotype1"
    assert build["datasetId"] == "f1_trio"
    assert build["missense"]["all"].expected == 2
    assert build["missense"]["rec"].expected == 1
    assert build["missense"]["male"].expected == 1
    assert build["missense"]["female"].expected == 1
