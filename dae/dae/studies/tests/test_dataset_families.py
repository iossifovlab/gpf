# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest

from dae.studies.study import GenotypeDataGroup
from dae.testing import (
    denovo_study,
    setup_dataset,
    setup_denovo,
    setup_pedigree,
)
from dae.testing.acgt_import import acgt_gpf

# from dae.pedigrees.loader import FamiliesLoader


@pytest.fixture()
def dataset(
    tmp_path: pathlib.Path,
) -> GenotypeDataGroup:
    root_path = tmp_path
    gpf_instance = acgt_gpf(root_path)
    var_path1 = setup_denovo(
        root_path / "study_1" / "in.tsv",
        """
familyId  location  variant    bestState
f1         chr1:1    sub(A->C) 2||2||1/0||0||1
        """)

    var_path2 = setup_denovo(
        root_path / "study_2" / "in.tsv",
        """
familyId  location  variant    bestState
f2        chr1:2    sub(A->C)  2||2||1/0||0||1
        """)

    ped_path1 = setup_pedigree(
        root_path / "study_1" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
        """))
    ped_path2 = setup_pedigree(
        root_path / "study_2" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f2       mom2     0     0     2   1      mom
f2       dad2     0     0     1   1      dad
f2       ch2      dad2  mom2  2   2      prb
        """))

    study1 = denovo_study(
        root_path,
        "study_1", ped_path1, [var_path1],
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
                            "source": "status",
                        },
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
                                "affected",
                            ],
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected",
                            ],
                        },
                    ],
                },
                "selected_person_set_collections": [
                    "phenotype",
                ],
            },
        })
    study2 = denovo_study(
        root_path,
        "study_2", ped_path2, [var_path2],
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
                            "source": "status",
                        },
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
                                "affected",
                            ],
                        },
                        {
                            "color": "#ffffff",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected",
                            ],
                        },
                    ],
                },
                "selected_person_set_collections": [
                    "phenotype",
                ],
            },
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
    tmp_path: pathlib.Path, dataset: GenotypeDataGroup,
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


def test_dataset_save_cached_families(
    tmp_path: pathlib.Path,
    dataset: GenotypeDataGroup,
) -> None:
    assert dataset._save_cached_families_data()
    assert (tmp_path / "dataset" / "families_cache.ped.gz").exists()


def test_dataset_load_cached_families(
    tmp_path: pathlib.Path,
    dataset: GenotypeDataGroup,
) -> None:
    assert dataset._save_cached_families_data()
    assert (tmp_path / "dataset" / "families_cache.ped.gz").exists()

    families = dataset._load_cached_families_data()
    assert families is not None

    all_persons = families.persons
    person = all_persons[("f1", "ch1")]
    assert person.get_attr("phenotype") == "developmental_disorder"

    person = all_persons[("f2", "ch2")]
    assert person.get_attr("phenotype") == "autism"

    person = all_persons[("f1", "dad1")]
    assert person.get_attr("phenotype") == "unaffected"


def test_dataset_save_cached_person_sets(
    tmp_path: pathlib.Path,
    dataset: GenotypeDataGroup,
) -> None:
    assert dataset._save_cached_person_sets()
    assert (
        tmp_path / "dataset" / "person_set_phenotype_cache.json.gz").exists()


def test_dataset_load_cached_person_sets(
    tmp_path: pathlib.Path,
    dataset: GenotypeDataGroup,
) -> None:
    assert dataset._save_cached_person_sets()
    assert (
        tmp_path / "dataset" / "person_set_phenotype_cache.json.gz").exists()

    pscs = dataset._load_cached_person_sets()
    assert pscs is not None

    psc = pscs["phenotype"]

    assert len(psc.person_sets["autism"]) == 1
    assert len(psc.person_sets["developmental_disorder"]) == 1
    assert len(psc.person_sets["unaffected"]) == 4
