# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

# from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.studies.study import GenotypeData

# @pytest.mark.parametrize(
#     "person_set,effect_types,count",
#     [
#         ("phenotype1", "missense", 2),
#         ("phenotype1", "synonymous", 2),
#         ("phenotype1", ["missense", "synonymous"], 4),
#         ("unaffected", "missense", 0),
#         ("unaffected", "synonymous", 1),
#         ("unaffected", ["missense", "synonymous"], 1),
#     ],
# )
# def test_get_variants(f1_trio, person_set, effect_types, count):
#     psc = f1_trio.get_person_set_collection("phenotype")
#     gh = GenotypeHelper(f1_trio, psc, person_set)

#     assert len(gh.get_variants(effect_types)) == count


@pytest.mark.parametrize(
    "person_set_id,male,female,unspecified,count",
    [
        ("phenotype1", 1, 1, 0, 2),
        ("unaffected", 0, 1, 0, 1),
    ],
)
def test_get_children_stats(
    f1_trio: GenotypeData,
    person_set_id: str,
    male: int, female: int, unspecified: int, count: int,
) -> None:
    psc = f1_trio.get_person_set_collection("phenotype")
    assert psc is not None

    # helper = GenotypeHelper(f1_trio, psc)

    children_stats = psc.person_sets[person_set_id].get_children_stats()

    assert children_stats.male == male
    assert children_stats.female == female
    assert children_stats.unspecified == unspecified
