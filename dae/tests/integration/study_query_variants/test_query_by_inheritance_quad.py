# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Union

import pytest

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, \
    vcf_study
from dae.testing.alla_import import alla_gpf
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.variants.attributes import Inheritance


@pytest.fixture(scope="module")
def quad_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_inheritance_quad{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        f1        ch2       dad1   mom1   2    2       sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 ch2
chrA   1   .  A   G     .    .      .    GT     0/0  0/0  0/0 0/0
chrA   2   .  A   G     .    .      .    GT     0/1  0/1  0/0 0/0
chrA   3   .  A   G     .    .      .    GT     1/0  1/0  0/0 0/0
chrA   4   .  A   G     .    .      .    GT     1/0  1/0  1/0 0/0
chrA   5   .  A   G     .    .      .    GT     1/0  1/0  0/1 0/0
chrA   6   .  A   G     .    .      .    GT     1/0  1/0  0/1 1/0
chrA   7   .  A   G     .    .      .    GT     0/0  1/1  1/0 0/0
chrA   8   .  A   G     .    .      .    GT     0/0  1/1  1/0 1/1
chrA   9   .  A   G     .    .      .    GT     0/0  1/1  1/1 1/1
chrA   10  .  A   G     .    .      .    GT     0/0  0/0  0/0 0/1
chrA   11  .  A   G     .    .      .    GT     1/1  1/1  1/0 1/1
        """)

    study = vcf_study(
        root_path,
        "inheritance_quad_vcf", pathlib.Path(ped_path),
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
        ("mendelian", 7),
        (["mendelian", "not possible_denovo"], 7),
        ("omission", 1),
        ("denovo", 1),
    ]
)
def test_inheritance_query_quad(
        quad_study: GenotypeData,
        inheritance: Union[str, list[str]],
        count: int) -> None:

    vs = list(
        quad_study.query_variants(
            inheritance=inheritance,
            return_reference=False)
    )
    for v in vs:
        print(v, "->", [a.inheritance_in_members for a in v.alt_alleles])
    assert len(vs) == count


@pytest.mark.parametrize(
    "region,count,inheritance",
    [
        (Region("chrA", 4, 9), 6, "mendelian"),
        (Region("chrA", 7, 7), 1, "omission"),
        (Region("chrA", 10, 10), 1, "denovo"),
        (Region("chrA", 1, 11), 10, "unknown"),
    ],
)
def test_inheritance_quad_full(
        quad_study: GenotypeData,
        region: Region, count: int, inheritance: str) -> None:
    vs = list(
        quad_study.query_variants(
            regions=[region], return_reference=False, return_unknown=False
        )
    )
    expected = Inheritance.from_name(inheritance)
    for v in vs:
        for aa in v.alt_alleles:
            print(aa, aa.inheritance_in_members)
            assert expected in aa.inheritance_in_members

    assert len(vs) == count
