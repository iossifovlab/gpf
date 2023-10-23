# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional, cast

import pytest

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, \
    vcf_study
from dae.variants.family_variant import FamilyAllele
from dae.testing.foobar_import import foobar_gpf
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData


@pytest.fixture(scope="module")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_genes_effects_{genotype_storage.storage_id}")
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom       0      0      2    1       mom
        f1        dad       0      0      1    1       dad
        f1        ch1       dad    mom    2    2       prb
        f1        ch2       dad    mom    1    1       sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=bar>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom dad ch1 ch2
bar    7   .  A   C,G,T .    .      .    GT     ./. ./. ./. ./.
bar    8   .  A   T,C,G .    .      .    GT     0/0 0/0 ./. 0/0
        """)

    study = vcf_study(
        root_path,
        "effects_trio_vcf", pathlib.Path(ped_path),
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
                }
            },
            "processing_config": {
                "include_reference": True
            }
        })
    return study


@pytest.mark.parametrize(
    "position,inheritance,effects,count",
    [
        (7, None, None, 1),
        (7, "unknown", None, 1),
        (7, "mendelian", None, 0),
        (7, "not unknown", None, 0),
        (7, None, ["synonymous", "missense"], 0),
    ],
)
def test_all_unknown_variants(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    effects: Optional[list[str]],
    count: int
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))
    gefs = [(v, v.effects) for v in vs]
    print(gefs)

    assert len(vs) == count


@pytest.mark.parametrize(
    "position,inheritance,effects,count",
    [
        (8, None, None, 1),
        (8, "unknown", None, 1),
        (8, "mendelian", None, 1),
        (8, "mendelian", ["synonymous"], 0),
        (8, "mendelian", ["missense"], 0),
        (8, "not denovo", None, 1),
        (8, "not omission", None, 1),
        (8, "not denovo or not omission", None, 1),
    ],
)
def test_unknown_and_reference(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    effects: Optional[list[str]],
    count: int
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))
    for v in vs:
        print(100 * "-")
        for aa in v.alleles:
            print(aa, cast(FamilyAllele, aa).inheritance_in_members)

    assert len(vs) == count


@pytest.mark.parametrize(
    "position,inheritance,return_reference,return_unknown,count",
    [
        (7, None, True, True, 1),
        (7, None, False, True, 0),
        (7, None, True, False, 0),
        (7, None, False, False, 0),
        (7, "denovo", False, False, 0),
        (7, "omission", False, False, 0),
        (7, "denovo", True, True, 0),
        (7, "omission", True, True, 0),
        (7, "unknown", True, True, 1),
        (7, "not denovo and not omission", False, False, 0),
        (7, "not denovo and not omission", False, True, 0),
        (7, "not denovo and not omission", True, True, 1),
    ],
)
def test_all_unknown_variants_return_reference_or_unknown(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    return_reference: bool,
    return_unknown: bool,
    count: int
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        inheritance=inheritance,
        return_unknown=return_unknown,
        return_reference=return_reference))

    assert len(vs) == count


@pytest.mark.parametrize(
    "position,inheritance,return_reference,return_unknown,count",
    [
        (8, None, True, True, 1),
        (8, None, True, False, 1),
        (8, None, False, True, 0),
        (8, None, False, False, 0),
        (8, "mendelian", True, False, 1),
        (8, "mendelian", False, False, 0),
        (8, "denovo", True, True, 0),
        (8, "omission", True, True, 0),
        (8, "not denovo and not omission", False, False, 0),
        (8, "not denovo and not omission", True, False, 1),
    ],
)
def test_reference_and_unknown_return_reference_or_unknown(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    return_reference: bool,
    return_unknown: bool,
    count: int
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        inheritance=inheritance,
        return_unknown=return_unknown,
        return_reference=return_reference))

    assert len(vs) == count
