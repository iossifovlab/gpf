# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

import pytest

from dae.testing import setup_pedigree, setup_vcf, \
    vcf_study
from dae.testing.alla_import import alla_gpf
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData


@pytest.fixture(scope="module")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_person_ids_{genotype_storage.storage_id}")
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
chrA   1   .  A   C     .    .      .    GT     0/0  0/0  0/0 0/0 0/0  0/1 0/0
chrA   2   .  A   C     .    .      .    GT     0/0  0/0  0/1 1/1 0/0  0/0 0/0
chrA   3   .  A   C     .    .      .    GT     0/0  0/1  0/0 1/1 0/1  0/0 0/0
        """)

    study = vcf_study(
        root_path,
        "psc_tios_vcf", pathlib.Path(ped_path),
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
        },
        study_config_update={
            "conf_dir": str(root_path / "study_1"),
            "person_set_collections": {
                "phenotype": {
                    "id": "phenotype",
                    "name": "Phenotype",
                    "sources": [
                        {
                            "from": "pedigree",
                            "source": "status"
                        }
                    ],
                    "default": {
                        "color": "#aaaaaa",
                        "id": "unspecified",
                        "name": "unspecified",
                    },
                    "domain": [
                        {
                            "color": "#ff0000",
                            "id": "autism",
                            "name": "autism",
                            "values": [
                                "affected"
                            ]
                        },
                        {
                            "color": "#ffffff",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected"
                            ]
                        },
                    ]
                },
                "selected_person_set_collections": [
                    "phenotype"
                ]
            }
        })
    return study


@pytest.mark.parametrize(
    "person_ids, count",
    [
        (None, 4),
        (["dad2"], 1),
        (["dad1"], 1),
        (["ch2"], 1),
        (["ch1"], 1),
        (["mom1"], 0),
        (["mom2"], 0),
    ]
)
def test_query_by_person_ids(
    imported_study: GenotypeData,
    person_ids: Optional[list[str]],
    count: int
) -> None:
    vs = list(imported_study.query_variants(
        person_ids=person_ids,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count


def test_study_build_person_set_collection(
    imported_study: GenotypeData,
) -> None:

    assert imported_study is not None
    psc = imported_study.person_set_collections["phenotype"]

    assert len(psc.person_sets["autism"]) == 2
    assert len(psc.person_sets["unaffected"]) == 4

    all_persons = imported_study.families.persons
    person = all_persons[("f1", "ch1")]
    assert person.get_attr("phenotype") == "autism"

    person = all_persons[("f2", "ch2")]
    assert person.get_attr("phenotype") == "autism"

    person = all_persons[("f1", "dad1")]
    assert person.get_attr("phenotype") == "unaffected"


@pytest.mark.parametrize(
    "person_set_collection, count",
    [
        (None, 4),
        (("phenotype", ["autism"]), 2),
        (("phenotype", ["unaffected"]), 2),
        (("phenotype", ["autism", "unaffected"]), 4),
    ]
)
def test_query_by_person_set_coolection(
    imported_study: GenotypeData,
    person_set_collection: Optional[tuple[str, list[str]]],
    count: int
) -> None:
    vs = list(imported_study.query_variants(
        person_set_collection=person_set_collection,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count
