# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from collections.abc import Callable

import pytest
from dae.genomic_resources.testing import (
    setup_pedigree,
    setup_vcf,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeDataGroup
from dae.testing.alla_import import alla_gpf
from dae.testing.import_helpers import (
    setup_dataset,
    vcf_study,
)


@pytest.fixture(scope="module")
def dataset(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeDataGroup:
    root_path = tmp_path_factory.mktemp(
        "test_dataset_query_by_person_set_collection")
    gpf_instance = alla_gpf(root_path, genotype_storage_factory(root_path))

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
##contig=<ID=chr1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1
chr1   1   .  A   C     .    .      .    GT     0/0  0/0  0/0
chr1   2   .  A   C     .    .      .    GT     0/0  0/0  0/1
chr1   3   .  A   C     .    .      .    GT     0/0  0/1  0/0
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
##contig=<ID=chr1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom2 dad2 ch2
chr1   4   .  A   C     .    .      .    GT     0/0  0/0  0/0
chr1   5   .  A   C     .    .      .    GT     0/0  0/0  0/1
chr1   6   .  A   C     .    .      .    GT     0/0  0/1  0/0
        """)

    study1 = vcf_study(
        root_path,
        "study_1", ped_path1, [vcf_path1],
        gpf_instance=gpf_instance,
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
                        "color": "#cccccc",
                        "id": "unknown",
                        "name": "unknown",
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
                        {
                            "color": "#aaaaaa",
                            "id": "unspecified",
                            "name": "unspecified",
                            "values": [
                                "unspecified",
                            ],
                        },
                    ],
                },
                "selected_person_set_collections": [
                    "phenotype",
                ],
            },
        })
    study2 = vcf_study(
        root_path,
        "study_2", ped_path2, [vcf_path2],
        gpf_instance=gpf_instance,
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
                        "color": "#cccccc",
                        "id": "unknown",
                        "name": "unknown",
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
                        {
                            "color": "#aaaaaa",
                            "id": "unspecified",
                            "name": "unspecified",
                            "values": [
                                "unspecified",
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
            conf_dir: {root_path / "dataset "}
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
                    - color: 'ff0000'
                      id: autism
                      name: autism
                      values:
                      - affected
                    - color: '#ffffff'
                      id: unaffected
                      name: unaffected
                      values:
                      - unaffected
                    - color: '#aaaaaa'
                      id: unspecified
                      name: unspecified
                      values:
                      - unspecified
                    default:
                      color: '#cccccc'
                      id: unknown
                      name: unknown
                selected_person_set_collections:
                - phenotype"""),
    )


def test_dataset_build_person_set_collection(
    dataset: GenotypeDataGroup,
) -> None:

    assert dataset is not None
    psc = dataset.person_set_collections["phenotype"]

    assert len(psc.person_sets["autism"]) == 1
    assert len(psc.person_sets["developmental_disorder"]) == 1
    assert len(psc.person_sets["unaffected"]) == 4

    all_persons = dataset.families.persons
    person = all_persons["f1", "ch1"]
    assert person.get_attr("phenotype") == "developmental_disorder"

    person = all_persons["f2", "ch2"]
    assert person.get_attr("phenotype") == "autism"

    person = all_persons["f1", "dad1"]
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
    ],
)
def test_query_by_person_ids(
    dataset: GenotypeDataGroup,
    person_ids: list[str] | None,
    count: int,
) -> None:
    vs = list(dataset.query_variants(
        person_ids=person_ids,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count


@pytest.mark.no_gs_impala
@pytest.mark.parametrize(
    "affected_statuses, count",
    [
        (None, 4),
        ("affected", 2),
        ("unaffected", 2),
        ("affected or unaffected", 4),
    ],
)
def test_query_by_affected_status(
    dataset: GenotypeDataGroup,
    affected_statuses: str | None,
    count: int,
) -> None:
    vs = list(dataset.query_variants(
        affected_statuses=affected_statuses,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count
