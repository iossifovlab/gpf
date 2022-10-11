# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.variants.attributes import Status
from dae.testing import setup_pedigree, setup_vcf, vcf_study

from ...alla_import import alla_gpf


@pytest.fixture(scope="module")
def imported_study(tmp_path_factory, genotype_storage):
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     2   1      sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  s1
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0
        chrA   2   .  A   T    .    .      .    GT     0/0 0/0 0/1 0/0
        chrA   3   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/1
        chrA   4   .  A   T,G  .    .      .    GT     1/0 2/0 0/0 0/0
        chrA   5   .  A   T,G  .    .      .    GT     1/0 2/0 2/0 0/0
        chrA   6   .  A   T,G  .    .      .    GT     1/0 2/0 1/0 0/0
        chrA   7   .  A   T,G  .    .      .    GT     1/0 2/0 1/2 0/0
        """)

    study = vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)
    return study


@pytest.mark.parametrize("region,seen_in_status", [
    (Region("chrA", 1, 1), Status.affected.value | Status.unaffected.value),
    (Region("chrA", 2, 2), Status.affected.value),
    (Region("chrA", 3, 3), Status.unaffected.value),
])
def test_summary_variants_seen_in_status_single_allele(
        region, seen_in_status, imported_study):

    svs = list(imported_study.query_summary_variants(regions=[region]))
    assert len(svs) == 1
    assert len(svs[0].alt_alleles) == 1
    aa = svs[0].alleles[1]
    assert aa.get_attribute("seen_in_status") == seen_in_status


@pytest.mark.inmemory
@pytest.mark.impala2
@pytest.mark.parametrize("region,seen_in_status", [
    (Region("chrA", 4, 4), [
        Status.unaffected.value,
        Status.unaffected.value]),
    (Region("chrA", 5, 5), [
        Status.unaffected.value,
        Status.affected.value | Status.unaffected.value]),
    (Region("chrA", 6, 6), [
        Status.affected.value | Status.unaffected.value,
        Status.unaffected.value]),
    (Region("chrA", 7, 7), [
        Status.affected.value | Status.unaffected.value,
        Status.affected.value | Status.unaffected.value]),
])
def test_summary_variants_seen_in_status_multi_allele(
        region, seen_in_status, imported_study):

    svs = list(imported_study.query_summary_variants(regions=[region]))
    assert len(svs) == 1
    assert len(svs[0].alt_alleles) == 2
    aa0, aa1 = svs[0].alt_alleles
    assert aa0.get_attribute("seen_in_status") == seen_in_status[0]
    assert aa1.get_attribute("seen_in_status") == seen_in_status[1]
