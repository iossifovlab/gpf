# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pathlib
from typing import Optional

import pytest

from dae.studies.study import GenotypeDataGroup
from dae.genotype_storage.genotype_storage import GenotypeStorage

from dae.testing import setup_pedigree, setup_dataset, \
    setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
# from dae.pedigrees.loader import FamiliesLoader


@pytest.fixture
def dataset(
    tmp_path: pathlib.Path,
    genotype_storage: GenotypeStorage
) -> GenotypeDataGroup:
    root_path = tmp_path
    gpf_instance = alla_gpf(root_path, genotype_storage)

    ped_path1 = setup_pedigree(
        root_path / "study_1" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
        """))

    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1
chrA   1   .  A   C     .    .      .    GT     0/0  0/0  0/0
chrA   2   .  A   C     .    .      .    GT     0/0  0/0  0/1
chrA   3   .  A   C     .    .      .    GT     0/0  0/1  0/0
        """)

    ped_path2 = setup_pedigree(
        root_path / "study_2" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f2       mom2     0     0     2   1      mom
f2       dad2     0     0     1   1      dad
f2       ch2      dad2  mom2  2   2      prb
        """))

    vcf_path2 = setup_vcf(
        root_path / "study_2" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom2 dad2 ch2
chrA   4   .  A   C     .    .      .    GT     0/0  0/0  0/0
chrA   5   .  A   C     .    .      .    GT     0/0  0/0  0/1
chrA   6   .  A   C     .    .      .    GT     0/0  0/1  0/0
        """)

    study1 = vcf_study(
        root_path,
        "study_1", ped_path1, [vcf_path1],
        gpf_instance,
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
                            "color": "#bbbbbb",
                            "id": "developmental_disorder",
                            "name": "developmental disorder",
                            "values": [
                                "affected"
                            ]
                        },
                        {
                            "color": "#00ff00",
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
    study2 = vcf_study(
        root_path,
        "study_2", ped_path2, [vcf_path2],
        gpf_instance,
        study_config_update={
            "conf_dir": str(root_path / "study_2"),
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

    (root_path / "dataset").mkdir(exist_ok=True)

    return setup_dataset(
        "ds1", gpf_instance, study1, study2,
        dataset_config_update=textwrap.dedent(f"""
            conf_dir: { root_path / "dataset "}
            person_set_collections:
                phenotype:
                    id: phenotype
                    name: Phenotype
                    sources:
                    - from: pedigree
                      source: status
                    domain:
                    - color: '#4b2626'
                      id: developmental_disorder
                      name: developmental disorder
                      values:
                      - affected
                    - color: '#ffffff'
                      id: unaffected
                      name: unaffected
                      values:
                      - unaffected
                    default:
                      color: '#aaaaaa'
                      id: unspecified
                      name: unspecified
                selected_person_set_collections:
                - phenotype"""))


def test_dataset_build_person_set_collection(
    dataset: GenotypeDataGroup
) -> None:

    assert dataset is not None
    psc = dataset.person_set_collections["phenotype"]

    assert len(psc.person_sets["autism"]) == 1
    assert len(psc.person_sets["developmental_disorder"]) == 1
    assert len(psc.person_sets["unaffected"]) == 4

    all_persons = dataset.families.persons
    person = all_persons[("f1", "ch1")]
    assert person.get_attr("phenotype") == "developmental_disorder"

    person = all_persons[("f2", "ch2")]
    assert person.get_attr("phenotype") == "autism"

    person = all_persons[("f1", "dad1")]
    assert person.get_attr("phenotype") == "unaffected"


@pytest.mark.parametrize(
    "person_ids, count",
    [
        (None, 4),
        (["dad1"], 1),
        (["dad2"], 1),
        (["ch1"], 1),
        (["ch2"], 1),
        (["mom1"], 0),
        (["mom2"], 0),
    ]
)
def test_query_by_person_ids(
    dataset: GenotypeDataGroup,
    person_ids: Optional[list[str]],
    count: int
) -> None:
    vs = list(dataset.query_variants(
        person_ids=person_ids,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count


@pytest.mark.parametrize(
    "person_set_collection, count",
    [
        (None, 4),
        (("phenotype", ["autism"]), 1),
        (("phenotype", ["developmental_disorder"]), 1),
        (("phenotype", ["unaffected"]), 2),
        (("phenotype", ["autism", "unaffected"]), 3),
        (("phenotype", ["developmental_disorder", "unaffected"]), 3),
        (("phenotype", ["autism", "developmental_disorder"]), 2),
        (("phenotype", ["autism", "developmental_disorder", "unaffected"]), 4),
    ]
)
def test_query_by_person_set_coolection(
    dataset: GenotypeDataGroup,
    person_set_collection: Optional[tuple[str, list[str]]],
    count: int
) -> None:
    vs = list(dataset.query_variants(
        person_set_collection=person_set_collection,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count
