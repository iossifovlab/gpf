# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.variants.attributes import Status

from ...foobar_import import setup_pedigree, setup_vcf
from ...foobar_import import foobar_vcf_study


@pytest.fixture(scope="module")
def imported_study(tmp_path_factory, genotype_storage):
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{genotype_storage.storage_id}")

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
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0
        foo    10  .  C   G   .    .      .    GT     0/0 0/0 0/1 0/0
        foo    11  .  C   G   .    .      .    GT     1/0 0/0 0/0 0/1
        """)

    study = foobar_vcf_study(
        root_path,
        "minimal_vcf", ped_path, vcf_path,
        genotype_storage)
    return study


@pytest.mark.impala
@pytest.mark.impala2
@pytest.mark.parametrize("region,count,seen_in_status", [
    (Region("foo", 7, 7), 1, Status.affected.value | Status.unaffected.value),
    (Region("foo", 10, 10), 1, Status.affected.value),
    (Region("foo", 11, 11), 1, Status.unaffected.value),
])
def test_query_summary_variants_seen_in_status(
        region, count, seen_in_status, imported_study):

    svs = list(imported_study.query_summary_variants(regions=[region]))
    assert len(svs) == count
    assert len(svs[0].alt_alleles) == 1
    aa = svs[0].alleles[1]
    assert aa.get_attribute("seen_in_status") == seen_in_status
