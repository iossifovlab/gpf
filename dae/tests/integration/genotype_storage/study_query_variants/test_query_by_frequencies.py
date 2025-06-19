# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import (
    denovo_study,
    setup_denovo,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from dae.testing.alla_import import alla_gpf


@pytest.fixture(scope="module")
def imported_vcf_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_by_frequencies")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        f2        mom2      0      0      2    1       mom
        f2        dad2      0      0      1    1       dad
        f2        ch2       dad2   mom2   2    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chrA   1   .  A   G     .    .      .    GT     0/1  0/0  0/0 0/0  0/0 0/1
chrA   2   .  A   G     .    .      .    GT     0/0  0/1  0/0 0/1  0/0 0/0
chrA   3   .  A   G     .    .      .    GT     0/0  0/0  0/0 0/1  0/0 0/0
chrA   4   .  A   G     .    .      .    GT     0/1  0/0  0/0 0/0  0/0 0/0
chrA   5   .  A   G     .    .      .    GT     1/1  1/1  0/0 1/1  0/0 1/1
chrA   6   .  A   G     .    .      .    GT     1/1  1/1  1/1 1/1  1/1 1/1
chrA   7   .  A   G     .    .      .    GT     0/0  0/0  1/1 0/0  1/1 0/0
chrA   8   .  A   G,T   .    .      .    GT     0/1  0/1  0/0 0/0  0/0 0/0
chrA   9   .  A   G,T   .    .      .    GT     0/2  0/2  0/0 0/0  0/0 0/0
chrA   10  .  A   G,T   .    .      .    GT     0/0  0/0  0/0 0/2  0/0 0/2
chrA   11  .  A   G,T   .    .      .    GT     0/0  0/0  0/0 0/1  0/0 0/1
chrA   12  .  A   G,T   .    .      .    GT     0/1  0/2  0/0 0/1  0/0 0/2
chrA   13  .  A   G,T,C .    .      .    GT     0/1  0/2  0/0 0/1  0/0 0/2

        """)

    return vcf_study(
        root_path,
        "test_query_by_frequencies", ped_path, [vcf_path],
        gpf_instance)


@pytest.mark.parametrize(
    "real_attr_filter,count",
    [
        (None, 20),
        ([("af_allele_count", (0, 0))], 2),
        ([("af_allele_count", (1, 1))], 2),
        ([("af_allele_freq", (100.0 / 8.0, 100.0 / 8.0))], 2),
        ([("af_allele_count", (1, 2))], 14),
        ([("af_allele_freq", (100.0 / 8.0, 200.0 / 8.0))], 14),
        ([("af_allele_count", (2, 2))], 12),
        ([("af_allele_freq", (200.0 / 8.0, 200.0 / 8.0))], 12),
        ([("af_allele_count", (3, 3))], 0),
        ([("af_allele_count", (3, None))], 4),
        ([("af_allele_freq", (300.0 / 8.0, None))], 4),
        ([("af_allele_count", (8, 8))], 4),
        ([("af_allele_freq", (100.0, 100.0))], 4),
    ],
)
def test_query_by_real_attr_frequency(
        real_attr_filter: list[tuple], count: int,
        imported_vcf_study: GenotypeData) -> None:
    vs = list(imported_vcf_study.query_variants(
        real_attr_filter=real_attr_filter))
    assert len(vs) == count


def test_query_by_ultra_rare(imported_vcf_study: GenotypeData) -> None:
    vs = list(imported_vcf_study.query_variants(ultra_rare=True))
    assert len(vs) == 4


@pytest.fixture(scope="module")
def imported_denovo_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_by_frequencies_denovo")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "denovo_data" / "in.ped",
        """
        familyId  personId  dadId   momId   sex   status  role  phenotype
        f1        f1.mom    0       0       2     1       mom   unaffected
        f1        f1.dad    0       0       1     1       dad   unaffected
        f1        f1.p1     f1.dad  f1.mom  1     2       prb   autism
        f1        f1.s1     f1.dad  f1.mom  2     2       sib   autism
        """)
    denovo_path = setup_denovo(
        root_path / "denovo_data" / "denovo.tsv",
        """
        chrom  pos  ref  alt  person_id
        chrA   1    A    T    f1.p1
        chrA   2    A    T    f1.p1
        chrA   3    A    T    f1.p1
        chrA   4    A    T    f1.p1
        """)

    return denovo_study(
        root_path,
        "helloworld", ped_path, [denovo_path],
        gpf_instance)


def test_query_denovo_variants_by_allele_frequency(
        imported_denovo_study: GenotypeData) -> None:
    vs = list(imported_denovo_study.query_variants(
        frequency_filter=[("af_allele_freq", (None, 100))]))
    assert len(vs) == 4
