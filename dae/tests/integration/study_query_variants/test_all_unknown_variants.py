# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

import pytest

from dae.testing import setup_pedigree, setup_vcf, \
    vcf_study
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
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=foo>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1
foo    14  .  C   T,A   .    .      .    GT     ./.  ./.  ./.
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


# (foo:14 C->T f1 110/110,
#     [missense!g1:missense!tx1:g1:missense:2/2(Pro->Ser)]),
@pytest.mark.parametrize(
    "effects, inheritance, count",
    [
        (None, None, 1),
        (None, "mendelian", 0),
        (None, "unknown", 1),
        (None, "not unknown", 0),
        ("missense", None, 0),
    ]
)
def test_all_unknown_variants(
    imported_study: GenotypeData,
    effects: Optional[list[str]],
    inheritance: str,
    count: int
) -> None:

    vs = list(imported_study.query_variants(
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))
    gefs = [(v, v.effects) for v in vs]
    print(gefs)

    assert len(vs) == count
