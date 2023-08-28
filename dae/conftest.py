# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional, Any
import pytest
from dae.genotype_storage.genotype_storage_registry import \
    GenotypeStorageRegistry, GenotypeStorage

pytest_plugins = ["dae_conftests.dae_conftests"]

def default_genotype_storage_configs(root_path: pathlib.Path) -> list[dict]:
    return [
        # DuckDb Storage
        {
            "id": "duckdb",
            "storage_type": "duckdb",
            "db": "duckdb_storage/dev_storage.db",
            "base_dir": str(root_path)
        },

        # DuckDb Parquet Storage
        {
            "id": "duckdb_parquet",
            "storage_type": "duckdb",
            "studies_dir": "duckdb_parquet",
            "base_dir": str(root_path)
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
            "dir": f"{root_path}/genotype_filesystem_data"
        },

    ]


GENOTYPE_STORAGE_REGISTRY = GenotypeStorageRegistry()
GENOTYPE_STORAGES: Optional[dict[str, Any]] = None


def _select_storages_by_type(
        storage_types: list[str]) -> dict[str, GenotypeStorage]:
    storages = {}
    for storage_id in GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        storage = GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(storage_id)
        if storage.get_storage_type() in storage_types:
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
        root_path = session\
            .config\
            ._tmp_path_factory.mktemp("genotype_storage")  # type: ignore
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
            with open(storage_config_filename, encoding="utf8") as infile:
                storage_config = yaml.safe_load(infile.read())
            storage = GENOTYPE_STORAGE_REGISTRY\
                .register_storage_config(storage_config)
            storage.start()
            GENOTYPE_STORAGES = {
                storage.storage_id: storage
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

    if hasattr(metafunc, "function"):
        marked_types = set()
        for mark in getattr(metafunc.function, "pytestmark", []):
            if mark.name.startswith("gs_"):
                marked_types.add(mark.name[3:])
        marked_types = marked_types & {
            "impala", "impala2", "duckdb", "inmemory", "gcp"}
        if marked_types:
            result = {}
            for storage_id, storage in GENOTYPE_STORAGES.items():
                if storage.get_storage_type() in marked_types:
                    result[storage_id] = storage

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
