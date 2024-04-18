# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region


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
        familyId personId dadId momId sex status role
        f1       mom      0     0     2   1      mom
        f1       dad      0     0     1   1      dad
        f1       ch1      dad   mom   2   2      prb
        f1       ch2      dad   mom   1   1      sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=foo>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom dad ch1 ch2
foo    14  .  C   T,A   .    .      .    GT     1/1 2/2 1/1 2/2
foo    15   . C   A,T   .    .      .    GT     1/1 0/0 0/1 0/0
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
                },
            },
            "processing_config": {
                "include_reference": True,
            },
        })
    return study


@pytest.mark.parametrize(
    "position, inheritance, effects, count",
    [
        (14, None, None, 1),
        (14, "omission", None, 1),
        (14, "denovo", None, 0),
        (14, "omission", ["synonymous"], 0),
        (14, "omission", ["missense"], 1),
        (14, "not omission and not mendelian and not unknown",
         ["missense"], 0),
        (14, "not omission", None, 1),
        (14, "not mendelian", None, 1),
    ],
)
def test_f1_non_cannonical_omission(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    effects: Optional[list[str]],
    count: int,
) -> None:

    region = Region("foo", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))

    assert len(vs) == count


@pytest.mark.parametrize(
    "position, inheritance, effects, count",
    [
        (15, None, None, 1),
        (15, "omission", None, 1),
        (15, "denovo", None, 0),
        (15, "not denovo", None, 1),
        (15, "not denovo", ["noEnd"], 1),
        (15, None, ["noEnd"], 1),
        (15, None, ["missense"], 0),
        (15, "omission", ["noEnd"], 1),
        (15, "mendelian", None, 1),
    ],
)
def test_f1_cannonical_omission(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    effects: Optional[list[str]],
    count: int,
) -> None:

    region = Region("foo", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))

    assert len(vs) == count


@pytest.mark.parametrize(
    "position,inheritance,return_reference,return_unknown,count",
    [
        (15, None, True, True, 1),
        (15, None, False, False, 1),  # find all
        (15, "denovo", False, False, 0),  # find denovo
        (15, "denovo", True, True, 0),  # find denovo
        (15, "omission", False, False, 1),  # find omission
        (15, "omission", True, True, 1),  # find omission
        (15, "mendelian", False, False, 1),
        (15, "mendelian", True, False, 1),
        (15, "mendelian", True, True, 1),
        (15, "not denovo and not omission and not unknown and not mendelian",
         False, False, 0),
        (15, "not denovo and not omission and not unknown and not mendelian",
         True, False, 0),
        (15, "not denovo and not omission",
         False, False, 0),
        (15, "not denovo and not omission",
         True, True, 1),
    ],
)
def test_f1_canonical_omission_return_reference_or_unknown(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    return_reference: bool,
    return_unknown: bool,
    count: int,
) -> None:
    region = Region("foo", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        inheritance=inheritance,
        return_unknown=return_unknown,
        return_reference=return_reference))
    assert len(vs) == count


@pytest.mark.parametrize(
    "position,inheritance,return_reference,return_unknown,count",
    [
        (14, None, True, True, 1),  # find all
        (14, None, False, False, 1),
        (14, "denovo", False, False, 0),  # find denovo
        (14, "not denovo and not omission and not unknown and not mendelian",
         False, False, 0),
        (14, "omission", False, False, 1),  # find omission
    ],
)
def test_f1_non_canonical_omission_return_reference_or_unknown(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    return_reference: bool,
    return_unknown: bool,
    count: int,
) -> None:
    region = Region("foo", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        inheritance=inheritance,
        return_unknown=return_unknown,
        return_reference=return_reference))
    assert len(vs) == count
