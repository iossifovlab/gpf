# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_by_person_ids")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId momId sex status role
        f1       mom1     0     0     2   1      mom
        f1       dad1     0     0     1   1      dad
        f1       ch1      dad1  mom1  2   2      prb
        f2       mom2     0     0     2   1      mom
        f2       dad2     0     0     1   1      dad
        f2       ch2      dad2  mom2  2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 mis dad2 ch2 mom2
chrA   1   .  A   C,G   .    .      .    GT     0/0  0/0  0/0 0/0 0/1  0/2 0/1
chrA   2   .  A   C     .    .      .    GT     0/1  0/0  0/0 1/1 0/0  0/0 0/1
chrA   3   .  A   C     .    .      .    GT     0/0  0/1  0/0 1/1 0/1  0/0 0/0
chrA   4   .  A   C     .    .      .    GT     0/0  0/0  0/0 0/0 0/1  0/0 0/0
chrA   5   .  A   C     .    .      .    GT     0/1  0/0  0/0 0/0 0/0  0/0 0/0
chrA   6   .  A   C     .    .      .    GT     1/1  1/1  0/0 0/0 1/1  0/0 1/1
chrA   7   .  A   C     .    .      .    GT     1/1  1/1  1/1 1/1 1/1  1/1 1/1
chrA   8   .  A   C     .    .      .    GT     0/0  0/0  1/1 1/1 0/0  1/1 0/0
chrA   9   .  A   C,G   .    .      .    GT     0/1  0/1  0/0 0/0 0/0  0/0 0/0
chrA   10   .  A   C,G   .    .      .    GT     0/2  0/2  0/0 0/0 0/0  0/0 0/0
chrA   11   .  A   C,G   .    .      .    GT     0/0  0/0  0/0 0/0 0/2  0/0 0/2
chrA   12   .  A   C,G   .    .      .    GT     0/0  0/0  0/0 0/0 0/1  0/0 0/1
chrA   13   .  A   C,G   .    .      .    GT     0/1  0/2  0/0 0/0 0/1  0/0 0/2
chrA   14   .  A   C,G,T .    .      .    GT     0/1  0/2  0/0 0/0 0/1  0/0 0/2
        """)

    return vcf_study(
        root_path,
        "tios_vcf", pathlib.Path(ped_path),
        [pathlib.Path(vcf_path)],
        gpf_instance,
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
            "processing_config": {
                "include_reference": True,
            },
        })


@pytest.mark.parametrize(
    "begin, end, person_ids, count",
    [
        (1, 1, None, 1),
        (1, 1, ["dad2"], 1),
        (1, 1, ["dad1"], 0),
        (1, 1, ["ch2"], 1),
        (1, 1, ["ch1"], 0),
        (2, 14, ["mom1"], 8),
        (2, 14, ["dad1"], 7),
        (2, 14, ["mom2"], 7),
        (2, 14, ["ch1"], 2),
        (2, 14, ["ch2"], 2),
        (2, 14, ["mom2", "ch2"], 8),
        (2, 14, ["mom1", "dad1"], 9),
        (2, 14, ["mom1"] * 10101 + ["dad1"], 9),
    ],
)
def test_query_by_person_ids(
    imported_study: GenotypeData,
    begin: int,
    end: int,
    person_ids: list[str] | None,
    count: int,
) -> None:
    region = Region("chrA", begin, end)
    vs = list(imported_study.query_variants(
        regions=[region],
        person_ids=person_ids,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count
