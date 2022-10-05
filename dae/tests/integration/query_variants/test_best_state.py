# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from tests.foobar_import import setup_vcf, setup_pedigree

from dae.utils.variant_utils import mat2str
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def best_state_vcf(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf_path")
    in_vcf = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT m1  d1  c1
foo    10  .  T   G,C   .    .      .    GT     0/1 0/0 0/0
foo    11  .  T   G,C   .    .      .    GT     0/2 0/0 0/0
foo    12  .  T   G,C   .    .      .    GT     0/0 0/0 0/0
foo    13  .  T   G,C   .    .      .    GT     0/. 0/0 0/0
foo    14  .  T   G,C   .    .      .    GT     0/1 0/2 0/0
foo    15  .  T   G,C,A .    .      .    GT     0/1 0/2 0/3
foo    16  .  T   G,C,A .    .      .    GT     0/1 0/2 0/0
        """)

    in_ped = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId momId sex status role
f1       m1       0     0     2    1     mom
f1       d1       0     0     1    1     dad
f1       c1       d1    m1    2    2     prb
f2       m2       0     0     2    1     mom
f2       d2       0     0     1    1     dad
f2       c2       d2    m2    2    2     prb
        """)
    return in_ped, in_vcf


@pytest.fixture(scope="module")
def imported_study(tmp_path_factory, best_state_vcf, genotype_storage):
    # pylint: disable=import-outside-toplevel
    from ...foobar_import import foobar_vcf_study

    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    ped_path, vcf_path = best_state_vcf

    return foobar_vcf_study(
        root_path, "best_state", ped_path, vcf_path, genotype_storage)


@pytest.mark.parametrize("region, exp_num_variants", [
    [Region("foo", 10, 10), 1],  # single allele
    [Region("foo", 12, 12), 0],  # all reference
])
def test_trios_multi(imported_study, region, exp_num_variants):

    variants = list(
        imported_study.query_variants(
            regions=[region],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == exp_num_variants
    for v in variants:
        assert v.best_state.shape == (3, 3)
        assert mat2str(v.best_state) == "122/100/000"
