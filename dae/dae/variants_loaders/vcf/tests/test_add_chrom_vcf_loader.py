# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.gpf_instance import GPFInstance
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import acgt_gpf, setup_pedigree, setup_vcf
from dae.utils.regions import Region
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture
def trio_families(
    tmp_path_factory: pytest.TempPathFactory,
) -> FamiliesData:
    root_path = tmp_path_factory.mktemp(
        "vcf_add_chrom_trio_families")
    ped_path = setup_pedigree(
        root_path / "trio_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        """)
    loader = FamiliesLoader(ped_path)
    return loader.load()


@pytest.fixture
def trio_gpf(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(
        "vcf_acgt_gpf_instance")
    return acgt_gpf(root_path)


@pytest.fixture
def trio_vcf(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp(
        "vcf_add_chrom_trio")
    return setup_vcf(
        root_path / "trio_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=1>
        ##contig=<ID=2>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1
        1      1   .  A   T    .    .      .    GT     0/1 0/0 0/1
        1      2   .  C   T    .    .      .    GT     0/1 0/0 0/1
        1      3   .  G   T    .    .      .    GT     0/1 0/0 0/1
        1      5   .  A   T    .    .      .    GT     0/1 0/0 0/1
        1      6   .  C   T    .    .      .    GT     0/1 0/0 0/1
        1      7   .  G   T    .    .      .    GT     0/1 0/0 0/1
        2      1   .  A   T    .    .      .    GT     0/1 0/0 0/1
        2      2   .  C   T    .    .      .    GT     0/1 0/0 0/1
        2      3   .  G   T    .    .      .    GT     0/1 0/0 0/1
        2      5   .  A   T    .    .      .    GT     0/1 0/0 0/1
        2      6   .  C   T    .    .      .    GT     0/1 0/0 0/1
        2      7   .  G   T    .    .      .    GT     0/1 0/0 0/1
        """)


@pytest.mark.parametrize(
    "region,count",
    [
        ("chr1:5-8", 3),
        ("chr2:1-4", 3),
        ("chr2:5-8", 3),
    ],
)
def test_add_chrom_reset_region(
    trio_families: FamiliesData,
    trio_gpf: GPFInstance,
    trio_vcf: pathlib.Path,
    region: str,
    count: int,
) -> None:

    loader = VcfLoader(
        trio_families, [str(trio_vcf)], trio_gpf.reference_genome,
        params={
            "add_chrom_prefix": "chr",
        })
    loader.reset_regions([Region.from_str(region)])
    alt_alleles = [
        sv.alt_alleles[0] for sv, _ in loader.full_variants_iterator()]

    assert len(alt_alleles) == count
