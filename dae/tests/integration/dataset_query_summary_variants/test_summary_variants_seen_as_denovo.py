# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, setup_dataset

from ...alla_import import alla_gpf, alla_vcf_study


@pytest.fixture(scope="module")
def imported_dataset(tmp_path_factory, genotype_storage):
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path1 = setup_pedigree(
        root_path / "study_1" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     1   1      sib
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  s1
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0
        chrA   2   .  A   T    .    .      .    GT     0/0 0/0 0/1 0/0
        chrA   3   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/1
        chrA   4   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/1
        chrA   5   .  A   T    .    .      .    GT     0/0 0/0 0/1 0/1
        chrA   6   .  A   T    .    .      .    GT     0/0 0/0 0/1 0/0
        chrA   7   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/1
        chrA   8   .  A   T    .    .      .    GT     0/0 1/0 0/0 0/1
        """)
    study1 = alla_vcf_study(
        root_path,
        "study_1", ped_path1, vcf_path1,
        gpf_instance)

    ped_path2 = setup_pedigree(
        root_path / "study_2" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     1   1      sib
        """)
    vcf_path2 = setup_vcf(
        root_path / "study_2" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  s1
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0
        chrA   2   .  A   T    .    .      .    GT     0/0 0/0 0/1 0/0
        chrA   3   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/1
        chrA   4   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/1
        chrA   5   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0
        chrA   6   .  A   T    .    .      .    GT     0/0 1/0 0/1 0/0
        chrA   7   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/1
        chrA   8   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/1
        """)

    study2 = alla_vcf_study(
        root_path,
        "study_2", ped_path2, vcf_path2,
        gpf_instance)

    return setup_dataset("ds1", gpf_instance, study1, study2)


@pytest.mark.impala
@pytest.mark.impala2
@pytest.mark.parametrize("region,seen_as_denovo", [
    (Region("chrA", 1, 1), False),
    (Region("chrA", 2, 2), True),
    (Region("chrA", 3, 3), False),
    (Region("chrA", 4, 4), True),
    (Region("chrA", 5, 5), True),
    (Region("chrA", 6, 6), True),
    (Region("chrA", 7, 7), True),
    (Region("chrA", 8, 8), True),
])
def test_summary_variants_seen_as_denovo_single_allele(
        region, seen_as_denovo, imported_dataset):

    svs = list(imported_dataset.query_summary_variants(regions=[region]))
    assert len(svs) == 1
    assert len(svs[0].alt_alleles) == 1
    aa = svs[0].alleles[1]
    assert aa.get_attribute("seen_as_denovo") == seen_as_denovo
