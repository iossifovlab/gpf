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
def multi_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_inheritance_multi{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId momId sex status role
f        gpa      0     0     1   1      maternal_grandfather
f        gma      0     0     2   1      maternal_grandmother
f        mom      gpa   gma   2   1      mom
f        dad      0     0     1   1      dad
f        ch1      dad   mom   2   2      prb
f        ch2      dad   mom   2   1      sib
f        ch3      dad   mom   2   1      sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
##contig=<ID=1>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT gma gpa mom dad ch1 ch2 ch3
chrA   1   .  A   T   .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/0 0/0
chrA   2   .  A   T   .    .      .    GT     0/1 0/0 0/0 0/0 0/0 0/0 0/0
chrA   3   .  A   T   .    .      .    GT     0/1 0/0 1/0 0/0 0/0 0/0 0/0
chrA   4   .  A   T   .    .      .    GT     0/1 0/0 1/0 0/0 0/1 0/0 0/0
chrA   5   .  A   T   .    .      .    GT     0/1 0/0 1/0 0/0 0/1 0/0 1/1
chrA   6   .  A   T   .    .      .    GT     0/0 0/0 1/0 0/0 0/1 0/0 1/1
chrA   7   .  A   T   .    .      .    GT     1/1 0/0 0/0 0/0 0/1 0/0 1/1
        """)

    study = vcf_study(
        root_path,
        "inheritance_multi_vcf", pathlib.Path(ped_path),
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
        (None, 6),
        ("mendelian", 4),
        ("omission", 1),
        ("denovo", 2),
    ]
)
def test_inheritance_query_multi(
        multi_study: GenotypeData,
        inheritance: Union[str, list[str]],
        count: int) -> None:

    vs = list(
        multi_study.query_variants(
            inheritance=inheritance,
            return_reference=False)
    )
    assert len(vs) == count


@pytest.mark.parametrize(
    "region,count,inheritance",
    [
        (Region("chrA", 3, 5), 3, "mendelian"),
        (Region("chrA", 6, 6), 1, "denovo"),
        (Region("chrA", 7, 7), 1, "omission"),
    ],
)
def test_inheritance_multi_full(
        multi_study: GenotypeData,
        region: Region,
        count: int, inheritance: str) -> None:
    vs = list(multi_study.query_variants(
        regions=[region], return_reference=False, return_unknown=False))

    expected = Inheritance.from_name(inheritance)
    for v in vs:
        for aa in v.alt_alleles:
            fa = cast(FamilyAllele, aa)
            assert expected in fa.inheritance_in_members

    assert len(vs) == count
