# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str


@pytest.fixture(scope="module")
def multi_vcf(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path, pathlib.Path]:
    root_path = tmp_path_factory.mktemp("vcf_path")
    in_vcf = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT m1  d1  c1
foo    10  .  T   G,C   .    .      .    GT     0/1 0/0 0/0
foo    12  .  T   G,C   .    .      .    GT     0/0 0/0 0/0
        """)

    in_ped = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId momId sex status role
f1       m1       0     0     2    1     mom
f1       d1       0     0     1    1     dad
f1       c1       d1    m1    2    2     prb
        """)
    return in_ped, in_vcf


@pytest.fixture(scope="module")
def multi_study(
    tmp_path_factory: pytest.TempPathFactory,
    multi_vcf: tuple[pathlib.Path, pathlib.Path],
    genotype_storage: GenotypeStorage,
) -> GenotypeData:
    # pylint: disable=import-outside-toplevel
    from dae.testing.foobar_import import foobar_gpf

    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    ped_path, vcf_path = multi_vcf

    return vcf_study(
        root_path, "best_state", ped_path, [vcf_path], gpf_instance)


@pytest.mark.parametrize("region, count, best_state", [
    [Region("foo", 10, 10), 1, "122/100/000"],  # first allele
    [Region("foo", 12, 12), 0, None],  # all reference
])
def test_trios_multi(
        multi_study: GenotypeData, region: Region, count: int,
        best_state: str | None) -> None:

    variants = list(
        multi_study.query_variants(
            regions=[region],
            return_reference=True,
            return_unknown=True,
        ),
    )
    assert len(variants) == count
    if count == 1:
        v = variants[0]
        assert v.best_state.shape == (3, 3)
        assert mat2str(v.best_state) == best_state
