import pytest

from dae.enrichment_tool.genotype_helper import GenotypeHelper


@pytest.mark.parametrize(
    "person_set,effect_types,count",
    [
        ("phenotype1", "missense", 2),
        ("phenotype1", "synonymous", 2),
        ("phenotype1", ["missense", "synonymous"], 4),
        ("unaffected", "missense", 0),
        ("unaffected", "synonymous", 1),
        ("unaffected", ["missense", "synonymous"], 1),
    ],
)
def test_get_variants(f1_trio, person_set, effect_types, count):
    psc = f1_trio.get_person_set_collection("phenotype")
    gh = GenotypeHelper(f1_trio, psc, person_set)

    assert len(gh.get_variants(effect_types)) == count


@pytest.mark.parametrize(
    "person_set,male,female,unspecified,count",
    [("phenotype1", 1, 1, 0, 2), ("unaffected", 0, 1, 0, 1),],
)
def test_get_children_stats(
    f1_trio, person_set, male, female, unspecified, count
):
    psc = f1_trio.get_person_set_collection("phenotype")
    gh = GenotypeHelper(f1_trio, psc, person_set)

    children_stats = gh.get_children_stats()

    assert len(children_stats) == count
    assert children_stats["M"] == male
    assert children_stats["F"] == female
    assert children_stats["U"] == unspecified

    children_stats = gh.get_children_stats()
    assert len(children_stats) == count
