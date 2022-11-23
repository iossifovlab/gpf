# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, vcf_study

from dae.testing.alla_import import alla_gpf


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
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/1
        chrA   2   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1
        chrA   3   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/0 0/0 0/0
        chrA   4   .  A   T    .    .      .    GT     0/1 0/0 0/0 0/1 0/0 0/0
        chrA   5   .  A   T,G  .    .      .    GT     0/1 0/0 0/0 0/2 0/0 0/0
        chrA   6   .  A   T,G  .    .      .    GT     0/1 2/0 0/0 0/2 0/0 0/0
        chrA   7   .  A   T,G  .    .      .    GT     0/1 2/0 0/0 0/1 0/0 0/0
        chrA   8   .  A   T,G  .    .      .    GT     0/1 2/0 0/0 0/1 2/0 0/0
        """)

    study = vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)
    return study


@pytest.mark.parametrize("region,family_variants_count", [
    (Region("chrA", 1, 1), 2),
    (Region("chrA", 2, 2), 1),
    (Region("chrA", 3, 3), 1),
    (Region("chrA", 4, 4), 2),
])
def test_summary_variants_family_variants_count_single_allele(
        region, family_variants_count, imported_study):

    svs = list(imported_study.query_summary_variants(regions=[region]))
    assert len(svs) == 1
    assert len(svs[0].alt_alleles) == 1
    aa = svs[0].alleles[1]
    assert aa.get_attribute("family_variants_count") == family_variants_count


@pytest.mark.inmemory
@pytest.mark.impala2(reason="supported for impala schema2")
@pytest.mark.parametrize("region,family_variants_count", [
    (Region("chrA", 5, 5), [1, 1]),
    (Region("chrA", 6, 6), [1, 2]),
    (Region("chrA", 7, 7), [2, 1]),
    (Region("chrA", 8, 8), [2, 2]),
])
def test_summary_variants_family_variants_count_multi_allele(
        region, family_variants_count, imported_study):

    svs = list(imported_study.query_summary_variants(regions=[region]))
    assert len(svs) == 1
    assert len(svs[0].alt_alleles) == 2
    aa0, aa1 = svs[0].alt_alleles
    assert aa0.get_attribute("family_variants_count") == \
        family_variants_count[0]
    assert aa1.get_attribute("family_variants_count") == \
        family_variants_count[1]


@pytest.mark.impala2(reason="supported for impala schema2")
@pytest.mark.parametrize("region,family_variants_count", [
    (Region("chrA", 5, 5), [1, 1]),
    (Region("chrA", 6, 6), [1, 2]),
    (Region("chrA", 7, 7), [2, 1]),
    (Region("chrA", 8, 8), [2, 2]),
])
def test_summary_variants_family_alleles_count_multi_allele(
        region, family_variants_count, imported_study):

    svs = list(imported_study.query_summary_variants(regions=[region]))
    assert len(svs) == 1
    assert len(svs[0].alt_alleles) == 2
    aa0, aa1 = svs[0].alt_alleles

    assert aa0.get_attribute("family_alleles_count") == \
        family_variants_count[0]
    assert aa1.get_attribute("family_alleles_count") == \
        family_variants_count[1]
