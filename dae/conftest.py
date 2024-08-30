# noqa: INP001
# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
from collections.abc import Callable
from typing import Any

import pytest

from dae.genotype_storage import get_genotype_storage_factory
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorage,
)

pytest_plugins = ["dae_conftests.dae_conftests"]


def _default_genotype_storage_configs(
    root_path: pathlib.Path,
) -> dict[str, dict[str, Any]]:

    localstack_host = os.environ.get("LOCALSTACK_HOST", "localhost")
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"  # noqa: S105
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"

    return {
        # Filesystem InMemory
        "inmemory": {
            "id": "inmemory",
            "storage_type": "inmemory",
            "dir": f"{root_path}/genotype_filesystem_data",
        },

        # Legacy DuckDb Storage
        "duckdb": {
            "id": "duckdb",
            "storage_type": "duckdb",
            "db": "duckdb_storage/storage.db",
            "base_dir": str(root_path),
            "read_only": False,
        },

        # DuckDb Parquet Storage
        "duckdb-parquet": {
            "id": "duckdb_parquet",
            "storage_type": "duckdb-parquet",
            "base_dir": str(root_path / "duckdb_parquet"),
        },

        # DuckDb S3 Parquet Storage
        "duckdb-s3-parquet": {
            "id": "duckdb_s3_parquet",
            "storage_type": "duckdb-s3-parquet",
            "bucket_url": f"s3:/{root_path}/duckdb_s3_parquet",
            "endpoint_url": f"http://{localstack_host}:4566/",
        },

        # # DuckDb2 Storage
        # {
        #     "id": "duckdb2",
        #     "storage_type": "duckdb2",
        #     "db": "duckdb2_storage/storage2.db",
        #     "base_dir": str(root_path),
        #     "read_only": False,
        # },
        # # DuckDb2 Parquet Inplace Storage
        # {
        #     "id": "duckdb2_inplace",
        #     "storage_type": "duckdb2",
        # },

        # # DuckDb Parquet Storage
        # {
        #     "id": "duckdb_parquet",
        #     "storage_type": "duckdb",
        #     "base_dir": str(root_path / "duckdb_parquet"),
        # },
        # # DuckDb Parquet Inplace Storage
        # {
        #     "id": "duckdb_inplace",
        #     "storage_type": "duckdb",
        # },

        # # Schema2 Parquet
        # {
        #     "id": "schema2_parquet",
        #     "storage_type": "parquet",
        #     "dir": str(root_path),
        # },
    }


def _default_storage_factory(
    storage_type: str,
) -> Callable[[pathlib.Path], GenotypeStorage]:
    def factory(root_path: pathlib.Path) -> GenotypeStorage:
        storage_configs = _default_genotype_storage_configs(root_path)
        assert storage_type in storage_configs
        storage_factory = get_genotype_storage_factory(storage_type)
        return storage_factory(storage_configs[storage_type])

    return factory


GENOTYPE_STORAGE_FACTORIES: dict[
    str, Callable[[pathlib.Path], GenotypeStorage]] = {}


def _select_storage_factories_by_type(
    storage_types: list[str],
) -> dict[str, Callable[[pathlib.Path], GenotypeStorage]]:
    storage_factories = {}
    for storage_type in storage_types:
        factory = _default_storage_factory(storage_type)
        if factory is None:
            raise ValueError(f"unsupported genotype storage type: {storage_type}")
        storage_factories[storage_type] = factory
    return storage_factories


def _populate_default_genotype_storage_factories(
) -> dict[str, Callable[[pathlib.Path], GenotypeStorage]]:
    default_storage_configs = _default_genotype_storage_configs(
        pathlib.Path.cwd())
    storage_factories = {}
    for storage_type in default_storage_configs:
        storage_factories[storage_type] = _default_storage_factory(storage_type)
    return storage_factories


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--gst",
        dest="storage_types",
        action="append",
        default=[],
        help="list of genotype storage types to use in integartion tests")

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
    global GENOTYPE_STORAGE_FACTORIES  # pylint: disable=global-statement

    if not GENOTYPE_STORAGE_FACTORIES:
        # pylint: disable=protected-access

        storage_types = session.config.getoption("storage_types")
        storage_config_filename = \
            session.config.getoption("storage_config")

        if storage_types:
            assert not storage_config_filename
            selected_storages = _select_storage_factories_by_type(storage_types)
            if not selected_storages:
                raise ValueError(
                    f"unsupported genotype storage type(s): {storage_types}")
            GENOTYPE_STORAGE_FACTORIES = selected_storages

        elif storage_config_filename:
            import yaml  # pylint: disable=import-outside-toplevel
            storage_config = yaml.safe_load(
                pathlib.Path(storage_config_filename).read_text())
            storage_type = storage_config["storage_type"]
            storage_factory = get_genotype_storage_factory(storage_type)

            def factory(_: pathlib.Path) -> GenotypeStorage:
                return storage_factory(storage_config)

            GENOTYPE_STORAGE_FACTORIES = {
                storage_type: factory,
            }
        else:
            GENOTYPE_STORAGE_FACTORIES = \
                _populate_default_genotype_storage_factories()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    # pylint: disable=too-many-branches
    # flake8: noqa: C901
    if "genotype_storage_factory" in metafunc.fixturenames:
        _generate_genotype_storage_fixtures(metafunc)
    if "grr_scheme" in metafunc.fixturenames:
        _generate_grr_schemes_fixtures(metafunc)


def _generate_genotype_storage_fixtures(metafunc: pytest.Metafunc) -> None:
    assert GENOTYPE_STORAGE_FACTORIES
    storage_factories = GENOTYPE_STORAGE_FACTORIES

    all_storage_types = {
        "inmemory",
        "duckdb", "duckdb2",
        "duckdb-parquet",
        "duckdb-s3-parquet",
        "impala", "impala2",
        "gcp",
        "parquet",
    }
    schema2_storage_types = {
        "duckdb", "duckdb2",
        "duckdb-parquet",
        "duckdb-s3-parquet",
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
                storage_type: factory
                for storage_type, factory in storage_factories.items()
                if (storage_type in marked_types)
            }

            storage_factories = result
        elif removed_types:
            result = {
                storage_type: factory
                for storage_type, factory in storage_factories.items()
                if (storage_type not in removed_types)
            }
            storage_factories = result

    metafunc.parametrize(
        "genotype_storage_factory",
        storage_factories.values(),
        ids=storage_factories.keys(),
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
