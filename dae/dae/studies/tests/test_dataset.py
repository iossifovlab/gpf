import os
import pytest
from dae.pedigrees.loader import FamiliesLoader
from dae.studies.study import GenotypeDataGroup


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), path
    )


def test_inheritance_trio_can_init(inheritance_trio_genotype_data_group):
    print("is inited")
    assert inheritance_trio_genotype_data_group is not None


def test_inheritance_trio_description(inheritance_trio_genotype_data_group):
    assert (
        inheritance_trio_genotype_data_group.description
        == "Sample description in markdown format.\n"
    )


def test_combine_families():
    families_A = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_B = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_B.ped")
    )
    new_families = GenotypeDataGroup._combine_families(
        families_A,
        families_B
    )

    merged_f1 = new_families["f1"]
    assert set(merged_f1.persons.keys()) == {
        "f1.mom",
        "f1.dad",
        "f1.p1",
        "f1.s1",
        "f1.s2",
    }


def test_combine_families_role_mismatch():
    families_A = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_C = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_C.ped")
    )
    with pytest.raises(AssertionError):
        GenotypeDataGroup._combine_families(
            families_A,
            families_C
        )


def test_combine_families_sex_mismatch():
    families_A = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_D = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_D.ped")
    )
    with pytest.raises(AssertionError):
        GenotypeDataGroup._combine_families(
            families_A,
            families_D
        )


def test_combine_families_sex_unspecified_mismatch():
    families_A = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_E = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_E.ped")
    )

    new_families = GenotypeDataGroup._combine_families(
            families_A,
            families_E
        )

    merged_f1 = new_families["f1"]
    assert set(merged_f1.persons.keys()) == {
        "f1.mom",
        "f1.dad",
        "f1.p1",
        "f1.s1",
        "f1.s2",
    }


def test_summary_variant_merging(fixtures_gpf_instance, data_import, variants_impala):
    genotype_data_group = fixtures_gpf_instance.get_genotype_data(
        "svmergingdataset"
    )
    assert genotype_data_group is not None
    vs = genotype_data_group.query_summary_variants()
    vs = list(vs)
    assert len(vs) == 4
