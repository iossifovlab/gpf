# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.testing import setup_pedigree, setup_vcf

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
        f1       s1       d1     m1     2   1      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1 0/0
        bar    11  .  C   G   .    .      .    GT     1/0 0/0 0/0 0/1
        bar    12  .  A   T   .    .      .    GT     0/0 1/0 1/0 0/0
        """)

    study = foobar_vcf_study(
        root_path,
        "minimal_vcf", ped_path, vcf_path,
        genotype_storage)
    return study


@pytest.mark.parametrize(
    "sexes,count",
    [
        (None, 4),
        ("male", 3),
        ("female", 2),
        ("male or female", 4),
        ("female and not male", 1),
        ("male and not female", 2),
        ("male and female", 1),
    ],
)
def test_query_by_sexes(
        sexes, count, imported_study):
    vs = imported_study.query_variants(sexes=sexes)
    vs = list(vs)
    assert len(vs) == count
