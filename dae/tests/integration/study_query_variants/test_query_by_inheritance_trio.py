# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Union, cast

import pytest

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, \
    vcf_study
from dae.testing.alla_import import alla_gpf
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele


@pytest.fixture(scope="module")
def trio_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_inheritance_trio_{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1
chrA   1   .  A   G     .    .      .    GT     0/0  0/0  0/0
chrA   2   .  A   G     .    .      .    GT     0/1  0/0  0/0
chrA   3   .  A   G     .    .      .    GT     1/0  0/0  0/0
chrA   4   .  A   G     .    .      .    GT     0/0  0/1  0/0
chrA   5   .  A   G     .    .      .    GT     0/0  1/0  0/0
chrA   6   .  A   G     .    .      .    GT     1/1  0/0  0/0
chrA   7   .  A   G     .    .      .    GT     0/0  1/1  0/0
chrA   8   .  A   G     .    .      .    GT     1/0  1/1  0/0
chrA   9   .  A   G     .    .      .    GT     1/1  1/0  0/0
chrA   10  .  A   G     .    .      .    GT     0/0  1/0  1/1
chrA   11  .  A   G     .    .      .    GT     0/0  0/0  1/0
chrA   12  .  A   G     .    .      .    GT     0/0  0/0  0/1
chrA   13  .  A   G     .    .      .    GT     1/1  1/1  0/1
chrA   14  .  A   G     .    .      .    GT     1/1  1/1  1/0
chrA   15  .  A   G     .    .      .    GT     1/.  1/1  1/0
        """)

    study = vcf_study(
        root_path,
        "inheritance_trio_vcf", pathlib.Path(ped_path),
        [vcf_path],
        gpf_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "include_reference_genotypes": True,
                    "include_unknown_family_genotypes": True,
                    "include_unknown_person_genotypes": True,
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                }
            },
            "processing_config": {
                "include_reference": True
            }
        })
    return study


@pytest.mark.parametrize(
    "inheritance,count",
    [
        ("mendelian", 3),
        (["mendelian"], 3),
        ("omission", 4),
        ("denovo", 2),
        ("unknown", 14),
    ],
)
def test_inheritance_query_trio(
        trio_study: GenotypeData,
        inheritance: Union[str, list[str]],
        count: int) -> None:

    vs = list(
        trio_study.query_variants(
            inheritance=inheritance,
            return_reference=False)
    )
    assert len(vs) == count


@pytest.mark.parametrize(
    "region,count,inheritance",
    [
        (Region("chrA", 13, 14), 2, "mendelian"),
        (Region("chrA", 10, 10), 1, "mendelian"),
        (Region("chrA", 6, 9), 4, "omission"),
        (Region("chrA", 11, 12), 2, "denovo"),
        (Region("chrA", 1, 15), 14, "unknown"),
        (Region("chrA", 2, 5), 4, "missing"),
    ],
)
def test_inheritance_trio_full(
        trio_study: GenotypeData,
        region: Region,
        count: int, inheritance: str) -> None:
    vs = list(trio_study.query_variants(
        regions=[region], return_reference=False, return_unknown=False))

    expected = Inheritance.from_name(inheritance)
    for v in vs:
        for aa in v.alt_alleles:
            fa = cast(FamilyAllele, aa)
            assert expected in fa.inheritance_in_members

    assert len(vs) == count
