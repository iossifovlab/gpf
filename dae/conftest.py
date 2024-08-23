# noqa: INP001
# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Any

import pytest

from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorage,
    GenotypeStorageRegistry,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData, GenotypeDataGroup
from dae.testing import setup_dataset, setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf

pytest_plugins = ["dae_conftests.dae_conftests"]


def default_genotype_storage_configs(root_path: pathlib.Path) -> list[dict]:
    return [
        # DuckDb2 Storage
        {
            "id": "duckdb2",
            "storage_type": "duckdb2",
            "db": "duckdb2_storage/storage2.db",
            "base_dir": str(root_path),
            "read_only": False,
        },
        # DuckDb2 Parquet Storage
        {
            "id": "duckdb2_parquet",
            "storage_type": "duckdb2",
            "base_dir": str(root_path / "duckdb_parquet"),
        },
        # DuckDb2 Parquet Inplace Storage
        {
            "id": "duckdb2_inplace",
            "storage_type": "duckdb2",
        },

        # DuckDb Storage
        {
            "id": "duckdb",
            "storage_type": "duckdb",
            "db": "duckdb_storage/storage.db",
            "base_dir": str(root_path),
            "read_only": False,
        },
        # DuckDb Parquet Storage
        {
            "id": "duckdb_parquet",
            "storage_type": "duckdb",
            "base_dir": str(root_path / "duckdb_parquet"),
        },
        # DuckDb Parquet Inplace Storage
        {
            "id": "duckdb_inplace",
            "storage_type": "duckdb",
        },

        # Filesystem InMemory
        {
            "id": "inmemory",
            "storage_type": "inmemory",
            "dir": f"{root_path}/genotype_filesystem_data",
        },

        # Schema2 Parquet
        {
            "id": "schema2_parquet",
            "storage_type": "parquet",
            "dir": str(root_path),
        },
    ]


GENOTYPE_STORAGE_REGISTRY = GenotypeStorageRegistry()
GENOTYPE_STORAGES: dict[str, Any] | None = None


@pytest.fixture(scope="module", params=["duckdb", "inmemory"])
def t4c8_instance(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(
        "study_group_person_set_queries_genotype_storages")

    storage_configs = {
        # DuckDb Storage
        "duckdb": {
            "id": "duckdb",
            "storage_type": "duckdb2",
            "db": "duckdb_storage/dev_storage.db",
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
                .register_storage_config(storage_config)

    genotype_storage = GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(
        request.param)
    assert genotype_storage is not None

    root_path = tmp_path_factory.mktemp(
        "study_group_person_set_queries")
    return t4c8_gpf(root_path, storage=genotype_storage)


@pytest.fixture(scope="module")
def t4c8_study_1(t4c8_instance: GPFInstance) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
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
    return vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        t4c8_instance,
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
        })


@pytest.fixture(scope="module")
def t4c8_study_2(t4c8_instance: GPFInstance) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
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
    return vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path1],
        t4c8_instance,
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
        })


@pytest.fixture()
def t4c8_dataset(
    t4c8_instance: GPFInstance,
    t4c8_study_1: GenotypeData,
    t4c8_study_2: GenotypeData,
) -> GenotypeDataGroup:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    (root_path / "dataset").mkdir(exist_ok=True)

    return setup_dataset(
        "dataset", t4c8_instance, t4c8_study_1, t4c8_study_2,
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


def _select_storages_by_type(
        storage_types: list[str]) -> dict[str, GenotypeStorage]:
    storages = {}
    for storage_id in GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        storage = GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(storage_id)
        if storage.storage_type in storage_types:
            storages[storage_id] = storage
    return storages


def _select_storages_by_ids(
        storage_ids: list[str]) -> dict[str, GenotypeStorage]:
    storages = {}
    for storage_id in GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        if storage_id in storage_ids:
            storages[storage_id] = \
                GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(storage_id)
    return storages


def _populate_storages_from_registry() -> dict[str, GenotypeStorage]:
    storages = {}
    for storage_id in GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        storages[storage_id] = \
            GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(storage_id)
    return storages


def _populate_default_genotype_storages(
        root_path: pathlib.Path) -> GenotypeStorageRegistry:
    if not GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        for storage_config in default_genotype_storage_configs(root_path):
            GENOTYPE_STORAGE_REGISTRY\
                .register_storage_config(storage_config)
    return GENOTYPE_STORAGE_REGISTRY


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--gst",
        dest="storage_types",
        action="append",
        default=[],
        help="list of genotype storage types to use in integartion tests")

    parser.addoption(
        "--gsi",
        dest="storage_ids",
        action="append",
        default=[],
        help="list of genotype storage IDs to use in integartion tests")

    parser.addoption(
        "--genotype-storage-config", "--gsf",
        dest="storage_config",
        default=None,
        help="genotype storage configuration file to use integration tests")

    parser.addoption(
        "--enable-s3-testing", "--s3",
        dest="enable_s3",
        action="store_true",
        default=False,
        help="enable S3 unit testing")

    parser.addoption(
        "--enable-http-testing", "--http",
        dest="enable_http",
        action="store_true",
        default=False,
        help="enable HTTP unit testing")


def pytest_sessionstart(session: pytest.Session) -> None:
    global GENOTYPE_STORAGES  # pylint: disable=global-statement
    if not GENOTYPE_STORAGES:
        # pylint: disable=protected-access
        root_path = session.config \
            ._tmp_path_factory.mktemp(  # type: ignore # noqa: SLF001
                "genotype_storage")

        _populate_default_genotype_storages(root_path)

        storage_types = session.config.getoption("storage_types")
        storage_ids = session.config.getoption("storage_ids")
        storage_config_filename = \
            session.config.getoption("storage_config")

        if storage_types:
            assert not storage_ids
            assert not storage_config_filename
            selected_storages = _select_storages_by_type(storage_types)
            if not selected_storages:
                raise ValueError(
                    f"unsupported genotype storage type(s): {storage_types}")
            GENOTYPE_STORAGES = selected_storages

        elif storage_ids:
            assert not storage_config_filename
            selected_storages = _select_storages_by_ids(storage_ids)
            if not selected_storages:
                raise ValueError(
                    f"unsupported genotype storage id(s): {storage_ids}")
            GENOTYPE_STORAGES = selected_storages
        elif storage_config_filename:
            import yaml  # pylint: disable=import-outside-toplevel
            storage_config = yaml.safe_load(
                pathlib.Path(storage_config_filename).read_text())
            storage = GENOTYPE_STORAGE_REGISTRY\
                .register_storage_config(storage_config)
            GENOTYPE_STORAGES = {
                storage.storage_id: storage,
            }
        else:
            GENOTYPE_STORAGES = _populate_storages_from_registry()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    # pylint: disable=too-many-branches
    # flake8: noqa: C901
    if "genotype_storage" in metafunc.fixturenames:
        _generate_genotype_storage_fixtures(metafunc)
    if "grr_scheme" in metafunc.fixturenames:
        _generate_grr_schemes_fixtures(metafunc)


def _generate_genotype_storage_fixtures(metafunc: pytest.Metafunc) -> None:
    assert GENOTYPE_STORAGES is not None
    storages = GENOTYPE_STORAGES
    all_storage_types = {
        "inmemory",
        "duckdb", "duckdb2",
        "impala", "impala2",
        "gcp",
        "parquet",
    }
    schema2_storage_types = {
        "duckdb", "duckdb2",
        "impala2",
        "gcp",
        "parquet",
    }

    if hasattr(metafunc, "function"):
        marked_types = set()
        removed_types = set()
        for mark in getattr(metafunc.function, "pytestmark", []):
            if mark.name.startswith("no_gs_"):
                storage_type = mark.name[6:]
                removed_types.add(storage_type)

            if mark.name.startswith("gs_"):
                storage_type = mark.name[3:]
                marked_types.add(storage_type)
                if storage_type == "duckdb":
                    marked_types.add("duckdb2")
                if storage_type == "schema2":
                    marked_types.update(schema2_storage_types)

        marked_types = marked_types & all_storage_types
        removed_types = removed_types & all_storage_types
        if marked_types:
            result = {
                storage_id: storage
                for storage_id, storage in storages.items()
                if (storage.storage_type in marked_types)
            }

            storages = result
        elif removed_types:
            result = {
                storage_id: storage
                for storage_id, storage in storages.items()
                if (storage.storage_type not in removed_types)
            }
            storages = result

    metafunc.parametrize(
        "genotype_storage",
        storages.values(),
        ids=storages.keys(),
        scope="module")


def _generate_grr_schemes_fixtures(metafunc: pytest.Metafunc) -> None:
    schemes = {"inmemory", "file"}
    if metafunc.config.getoption("enable_s3"):
        schemes.add("s3")
    if metafunc.config.getoption("enable_http"):
        schemes.add("http")

    if hasattr(metafunc, "function"):
        marked_schemes = set()
        for mark in getattr(metafunc.function, "pytestmark", []):
            if mark.name.startswith("grr_"):
                marked_schemes.add(mark.name[4:])
        if "rw" in marked_schemes:
            marked_schemes.add("file")
            marked_schemes.add("s3")
            marked_schemes.add("inmemory")
        if "full" in marked_schemes:
            marked_schemes.add("file")
            marked_schemes.add("s3")
        if "tabix" in marked_schemes:
            marked_schemes.add("file")
            marked_schemes.add("s3")
            marked_schemes.add("http")

        marked_schemes = marked_schemes & {
            "file", "inmemory", "http", "s3"}
        if marked_schemes:
            schemes = schemes & marked_schemes
    metafunc.parametrize(
        "grr_scheme",
        schemes,
        scope="module")
