# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import time

import pytest
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), path
    )


def test_inheritance_trio_can_init(inheritance_trio_genotype_data_group):
    print("is inited")
    assert inheritance_trio_genotype_data_group is not None


def test_combine_families():
    families_a = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_b = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_B.ped")
    )
    new_families = FamiliesData.combine(
        families_a,
        families_b,
        forced=False
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
    families_a = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_c = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_C.ped")
    )
    with pytest.raises(AssertionError):
        FamiliesData.combine(
            families_a,
            families_c,
            forced=False
        )


def test_combine_families_sex_mismatch():
    families_a = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_d = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_D.ped")
    )
    with pytest.raises(AssertionError):
        FamiliesData.combine(
            families_a,
            families_d,
            forced=False
        )


def test_combine_families_sex_unspecified_mismatch():
    families_a = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_A.ped")
    )
    families_e = FamiliesLoader.load_pedigree_file(
        relative_to_this_test_folder("fixtures/pedigree_E.ped")
    )

    new_families = FamiliesData.combine(
        families_a,
        families_e,
        forced=False,
    )

    merged_f1 = new_families["f1"]
    assert set(merged_f1.persons.keys()) == {
        "f1.mom",
        "f1.dad",
        "f1.p1",
        "f1.s1",
        "f1.s2",
    }


def test_summary_variant_merging(
        fixtures_gpf_instance, data_import, variants_impala):
    genotype_data_group = fixtures_gpf_instance.get_genotype_data(
        "svmergingdataset"
    )
    assert genotype_data_group is not None
    variants = genotype_data_group.query_summary_variants()
    variants = list(sorted(variants, key=lambda v: v.position))

    # TODO expected?
    assert variants[0].get_attribute("family_variants_count")[0] == 9
    assert variants[1].get_attribute("seen_as_denovo")[0] is True
    assert variants[1].get_attribute("seen_in_status")[0] == 3
    assert len(variants) == 4


def test_can_close_study_group_query(
        fixtures_gpf_instance, data_import, variants_impala):
    genotype_data_group = fixtures_gpf_instance.get_genotype_data(
        "svmergingdataset"
    )
    assert genotype_data_group is not None

    variants = genotype_data_group.query_variants()

    for variant in variants:
        print(variant)
        break

    variants.close()
    time.sleep(1)
