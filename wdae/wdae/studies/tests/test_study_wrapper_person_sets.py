# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from pathlib import Path
from typing import Any

import pytest
from dae.duckdb_storage.duckdb_genotype_storage import duckdb_storage_factory
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.testing.alla_import import alla_gpf
from dae.testing.import_helpers import setup_dataset, vcf_study
from gpf_instance.gpf_instance import WGPFInstance

from studies.query_transformer import QueryTransformer, make_query_transformer
from studies.study_wrapper import WDAEStudyGroup


@pytest.fixture(scope="module")
def instance_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("test_unique_family_variants_query")


@pytest.fixture(scope="module")
def wgpf_instance(instance_path: Path) -> WGPFInstance:
    storage_config = {
        "id": "duckdb",
        "storage_type": "duckdb",
        "db": "duckdb2_storage/storage2.db",
        "base_dir": str(instance_path),
    }
    gpf_instance = alla_gpf(
        instance_path, duckdb_storage_factory(storage_config),
    )

    return WGPFInstance(
        gpf_instance.dae_config,
        gpf_instance.dae_dir,
        gpf_instance.dae_config_path,
        grr=gpf_instance.grr,
    )


@pytest.fixture(scope="module")
def dataset(
    instance_path: Path,
    wgpf_instance: WGPFInstance,
) -> WDAEStudyGroup:
    root_path = instance_path

    ped_path1 = setup_pedigree(
        root_path / "study_1" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f2       mom2     0     0     2   1      mom
f2       dad2     0     0     1   1      dad
f2       ch2      dad2  mom2  2   2      prb
        """))

    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chr1   1   .  A   C,G   .    .      .    GT     0/1  0/2  1/0 0/1  1/0 0/0
chr1   2   .  A   C     .    .      .    GT     0/0  0/1  0/0 0/1  0/0 0/1
        """)

    ped_path2 = setup_pedigree(
        root_path / "study_2" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
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
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chr1   1   .  A   C,G   .    .      .    GT     0/1  0/2  0/0 0/0  0/1 0/0
chr1   2   .  A   C     .    .      .    GT     0/1  0/0  0/0 0/1  0/0 0/1
        """)

    study1 = vcf_study(
        root_path,
        "study_1", ped_path1, [vcf_path1],
        gpf_instance=wgpf_instance,
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
        gpf_instance=wgpf_instance,
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

    wgpf_instance.reload()

    setup_dataset(
        "ds1", wgpf_instance, study1, study2,
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
                - phenotype""",
        ),
    )

    wrapper = wgpf_instance.get_wdae_wrapper("ds1")
    assert isinstance(wrapper, WDAEStudyGroup)

    return wrapper


@pytest.fixture(scope="module")
def query_transformer(
    wgpf_instance: WGPFInstance,
) -> QueryTransformer:
    return make_query_transformer(wgpf_instance)


@pytest.mark.parametrize(
    "person_set_collection, count",
    [
        ({"id": "phenotype", "checkedValues": ["autism"]}, 1),
        ({"id": "phenotype", "checkedValues": ["developmental_disorder"]}, 2),
    ],
)
def test_person_set_collection_queries(
    dataset: WDAEStudyGroup,
    query_transformer: QueryTransformer,
    person_set_collection: dict[str, Any],
    count: int,
) -> None:
    query: dict[str, Any] = {"personSetCollection": person_set_collection}
    vs = list(dataset.query_variants_raw(query, query_transformer))

    assert len(vs) == count
