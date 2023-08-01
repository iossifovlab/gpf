# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import time

import pytest
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData
from dae.studies.study import GenotypeData

from dae.testing import setup_pedigree, setup_vcf, setup_dataset, vcf_study
from dae.testing.acgt_import import acgt_gpf


def relative_to_this_test_folder(path: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), path
    )


def test_inheritance_trio_can_init(
        inheritance_trio_genotype_data_group: GenotypeData) -> None:
    print("is inited")
    assert inheritance_trio_genotype_data_group is not None


def test_combine_families() -> None:
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


def test_combine_families_role_mismatch() -> None:
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


def test_combine_families_sex_mismatch() -> None:
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


def test_combine_families_sex_unspecified_mismatch() -> None:
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


@pytest.fixture(scope="module")
def svmergingdataset(tmp_path_factory: pytest.TempPathFactory) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "svnmergindataset")
    gpf_instance = acgt_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f3       mom3     0     0     2   1      mom
f3       dad3     0     0     1   1      dad
f3       ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   1   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
chr1   2   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1
chr1   3   .  G   T   .    .      .    GT     0/0  1/0  0/1 0/0  0/0  0/0
        """)  # noqa
    vcf_path2 = setup_vcf(
        root_path / "study_2" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   1   .  A   C   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1
chr1   2   .  C   G   .    .      .    GT     0/1  0/1  0/1 0/0  0/0  0/0
chr1   4   .  T   A   .    .      .    GT     0/0  0/0  0/0 0/1  0/0  0/0
        """)  # noqa

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            }
        },
    }
    study1 = vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        gpf_instance,
        project_config_update=project_config_update)
    study2 = vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path2],
        gpf_instance,
        project_config_update=project_config_update)

    return setup_dataset("ds1", gpf_instance, study1, study2)


def test_summary_variant_merging(svmergingdataset: GenotypeData) -> None:
    genotype_data_group = svmergingdataset
    assert genotype_data_group is not None
    variants = list(genotype_data_group.query_summary_variants())
    variants = list(sorted(variants, key=lambda v: v.position))  # type: ignore

    assert [
        a.get_attribute("family_variants_count")
        for v in variants for a in v.alt_alleles
    ] == [2, 2, 1, 1]
    assert [
        a.get_attribute("seen_as_denovo")
        for v in variants for a in v.alt_alleles
    ] == [True, True, False, False]
    assert [
        a.get_attribute("seen_in_status")
        for v in variants for a in v.alt_alleles
    ] == [2, 3, 3, 1]

    assert len(variants) == 4


def test_can_close_study_group_query(svmergingdataset: GenotypeData) -> None:
    genotype_data_group = svmergingdataset
    assert genotype_data_group is not None

    variants = genotype_data_group.query_variants()

    for variant in variants:
        print(variant)
        break

    variants.close()
    time.sleep(1)
