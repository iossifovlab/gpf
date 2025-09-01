# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Any, cast

import pytest
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.gpf_instance import GPFInstance
from dae.person_sets import PSCQuery
from dae.testing import setup_dataset, setup_pedigree, setup_vcf, vcf_study
from dae.testing.acgt_import import acgt_gpf
from gpf_instance.gpf_instance import WGPFInstance

from studies.query_transformer import QueryTransformer, make_query_transformer
from studies.response_transformer import (
    ResponseTransformer,
    make_response_transformer,
)
from studies.study_wrapper import WDAEStudy, WDAEStudyGroup

GENOTYPE_STORAGE_REGISTRY = GenotypeStorageRegistry()


@pytest.fixture(scope="module", params=["duckdb", "inmemory"])
def gpf_fixture(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(
        "study_group_person_set_queries_genotype_storages")

    storage_configs = {
        # DuckDb Storage
        "duckdb": {
            "id": "duckdb",
            "storage_type": "duckdb_parquet",
            "base_dir": str(root_path),
        },

        # Filesystem InMemory
        "inmemory": {
            "id": "inmemory",
            "storage_type": "inmemory",
            "dir": f"{root_path}/genotype_filesystem_data",
        },
    }

    if not GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        for storage_config in storage_configs.values():
            GENOTYPE_STORAGE_REGISTRY\
                .register_storage_config(
                    cast(dict[str, Any], storage_config))

    genotype_storage = GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(
        request.param)
    assert genotype_storage is not None

    root_path = tmp_path_factory.mktemp(
        "study_group_person_set_queries")
    return acgt_gpf(root_path, storage=genotype_storage)


@pytest.fixture(scope="module")
def wgpf_fixture(
    gpf_fixture: GPFInstance,
) -> WGPFInstance:
    grr = gpf_fixture.grr
    root_path = pathlib.Path(gpf_fixture.dae_dir)
    instance_filename = str(root_path / "gpf_instance.yaml")
    return WGPFInstance.build(instance_filename, grr=grr)


@pytest.fixture(scope="module")
def study_1(wgpf_fixture: WGPFInstance) -> WDAEStudy:
    root_path = pathlib.Path(wgpf_fixture.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   1   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
chr1   2   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1
chr1   3   .  G   T   .    .      .    GT     0/0  1/0  0/1 0/0  0/0  0/0
        """)

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            },
        },
    }
    return WDAEStudy(wgpf_fixture.genotype_storages, vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        gpf_instance=wgpf_fixture,
        project_config_update=project_config_update,
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
                            "id": "autism",
                            "name": "autism",
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
        },
    ), None)


@pytest.fixture(scope="module")
def study_2(wgpf_fixture: WGPFInstance) -> WDAEStudy:
    root_path = pathlib.Path(wgpf_fixture.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_2" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f2.1     mom1     0     0     2   1      mom
f2.1     dad1     0     0     1   1      dad
f2.1     ch1      dad1  mom1  2   2      prb
f2.3     mom3     0     0     2   1      mom
f2.3     dad3     0     0     1   1      dad
f2.3     ch3      dad3  mom3  2   2      prb
f2.3     ch4      dad3  mom3  2   0      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_2" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3 ch4
chr1   5   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0 0/1
chr1   6   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1 0/0
chr1   7   .  G   T   .    .      .    GT     0/0  1/0  0/1 0/0  0/0  0/0 0/1
        """)

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            },
        },
    }
    return WDAEStudy(wgpf_fixture.genotype_storages, vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path1],
        gpf_instance=wgpf_fixture,
        project_config_update=project_config_update,
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
                            "color": "#bbbbbb",
                            "id": "epilepsy",
                            "name": "epilepsy",
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
        },
    ), None)


@pytest.fixture
def dataset(
    wgpf_fixture: WGPFInstance,
    study_1: WDAEStudy,
    study_2: WDAEStudy,
) -> WDAEStudyGroup:
    root_path = pathlib.Path(wgpf_fixture.dae_dir)
    (root_path / "dataset").mkdir(exist_ok=True)

    return WDAEStudyGroup(wgpf_fixture.genotype_storages, setup_dataset(
        "dataset", wgpf_fixture,
        study_1.genotype_data, study_2.genotype_data,
        dataset_config_update=textwrap.dedent(f"""
            conf_dir: {root_path / "dataset "}
            genotype_browser:
              enabled: true
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
                - phenotype""",
        ),
    ), None, children=[study_1, study_2])


@pytest.fixture
def query_transformer(wgpf_fixture: WGPFInstance) -> QueryTransformer:
    return make_query_transformer(wgpf_fixture)


@pytest.fixture
def response_transformer(wgpf_fixture: WGPFInstance) -> ResponseTransformer:
    return make_response_transformer(wgpf_fixture)


def test_dataset_simple(dataset: WDAEStudyGroup) -> None:
    assert dataset is not None
    assert dataset.person_set_collections
    assert "phenotype" in dataset.person_set_collections
    psc = dataset.get_person_set_collection("phenotype")
    assert psc is not None

    assert "autism" in psc.person_sets
    assert "epilepsy" in psc.person_sets
    assert "unaffected" in psc.person_sets
    assert "unspecified" in psc.person_sets


@pytest.mark.parametrize(
    "psc_query, count", [
        (PSCQuery("phenotype", {"epilepsy"}), 3),
        (PSCQuery("phenotype", {"autism"}), 3),
        (PSCQuery("phenotype", {"unaffected"}), 2),
        (PSCQuery("phenotype", {"unspecified"}), 2),
        (PSCQuery("phenotype", {"epilepsy", "autism"}), 6),
        (PSCQuery("phenotype", {"unaffected", "autism"}), 4),
        (PSCQuery("phenotype", {"epilepsy", "autism", "unaffected"}), 6),
        (PSCQuery(
            "phenotype",
            {"epilepsy", "autism", "unaffected", "unspecified"}), 8),
    ],
)
def test_dataset_person_sets_queries(
    dataset: WDAEStudy,
    query_transformer: QueryTransformer,
    response_transformer: ResponseTransformer,
    psc_query: PSCQuery,
    count: int,
) -> None:
    vs = list(dataset.query_variants_wdae(
        {
            "personSetCollection": {
                "id": psc_query.psc_id,
                "checkedValues": psc_query.selected_person_sets,
            },
        }, [],
        query_transformer, response_transformer,
    ))
    assert len(vs) == count
