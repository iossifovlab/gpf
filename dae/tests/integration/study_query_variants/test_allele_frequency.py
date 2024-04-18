# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

import pytest

from dae.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def freq_vcf(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path, pathlib.Path]:
    root_path = tmp_path_factory.mktemp("vcf_path")
    in_vcf = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=foo>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1  mis d2  c2  m2
foo    10  .  T   G     .    .      .    GT   0/1 0/0 0/0 1/1 0/0 0/0 0/1
foo    11  .  T   G     .    .      .    GT   0/0 0/1 0/0 1/1 0/1 0/0 0/0
foo    12  .  T   G     .    .      .    GT   0/0 0/0 0/0 0/0 0/1 0/0 0/0
foo    13  .  T   G     .    .      .    GT   0/1 0/0 0/0 0/0 0/0 0/0 0/0
foo    14  .  T   G     .    .      .    GT   1/1 1/1 0/0 0/0 1/1 0/0 1/1
foo    15  .  T   G     .    .      .    GT   1/1 1/1 1/1 1/1 1/1 1/1 1/1
foo    16  .  T   G     .    .      .    GT   0/0 0/0 1/1 1/1 0/0 1/1 0/0
foo    17  .  T   G,A   .    .      .    GT   0/1 0/1 0/0 0/0 0/0 0/0 0/0
foo    18  .  T   G,A   .    .      .    GT   0/2 0/2 0/0 0/0 0/0 0/0 0/0
foo    19  .  T   G,A   .    .      .    GT   0/0 0/0 0/0 0/0 0/2 0/0 0/2
foo    20  .  T   G,A   .    .      .    GT   0/0 0/0 0/0 0/0 0/1 0/0 0/1
foo    21  .  T   G,A   .    .      .    GT   0/1 0/2 0/0 0/0 0/1 0/0 0/2
bar    11  .  T   G     .    .      .    GT   ./. 0/2 0/0 0/0 0/1 0/1 0/0
        """)

    in_ped = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId	momId sex status role
f1       m1       0     0     2   1      mom
f1       d1       0     0     1   1      dad
f1       c1       d1    m1    2   2      prb
f2       m2       0     0     2   1      mom
f2       d2       0     0     1   1      dad
f2       c2       d2    m2    2   2      prb
        """)

    return in_ped, in_vcf


@pytest.fixture(scope="module")
def freq_study(
    tmp_path_factory: pytest.TempPathFactory,
    freq_vcf: tuple[pathlib.Path, pathlib.Path],
    genotype_storage: GenotypeStorage,
) -> GenotypeData:
    # pylint: disable=import-outside-toplevel
    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path, vcf_path = freq_vcf

    study = vcf_study(
        root_path, "freq_vcf", ped_path, [vcf_path], gpf_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "include_reference_genotypes": True,
                    "include_unknown_family_genotypes": True,
                    "include_unknown_person_genotypes": True,
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
        })
    return study


@pytest.mark.parametrize("region,count,freqs", [
    # # single alt allele
    (Region("foo", 10, 10), 2, [None, 25.0]),
    (Region("foo", 11, 11), 2, [None, 25.0]),
    (Region("foo", 12, 12), 1, [None, 12.5]),
    (Region("foo", 13, 13), 1, [None, 12.5]),
    (Region("foo", 14, 14), 2, [None, 100.0]),
    (Region("foo", 15, 15), 2, [None, 100.0]),
    (Region("foo", 16, 16), 2, [None, 0.0]),
    # # multiple alt alleles
    (Region("foo", 17, 17), 1, [None, 25.0]),
    (Region("foo", 18, 18), 1, [None, 25.0]),
    (Region("foo", 19, 19), 1, [None, 25.0]),
    (Region("foo", 20, 20), 1, [None, 25.0]),
    (Region("foo", 21, 21), 2, [None, 25.0, 25.0]),
    # multiple variants
    (Region("foo", 10, 11), 4, [None, 25.0]),
    # unknown genotypes
    (Region("bar", 11, 11), 1, [None, 25.0]),
    # no alleles
    (Region("bar", 30, 30), 0, []),
])
def test_variant_frequency_queries(
        freq_study: GenotypeData, region: Region, count: int,
        freqs: list[Optional[float]]) -> None:

    fvs = list(freq_study.query_variants(regions=[region]))
    assert len(fvs) == count

    for v in fvs:
        assert freqs[1:] == v.frequencies[1:]
