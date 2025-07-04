# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
from collections.abc import Callable
from typing import Any, cast

import pytest
import pytest_mock

from dae.genomic_resources.genomic_context import (
    GenomicContext,
    get_genomic_context,
    register_context,
)
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorage,
    get_genotype_storage_factory,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.gpf_instance_plugin.gpf_instance_context_plugin import (
    GPFInstanceGenomicContext,
)


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
        "duckdb_legacy": {
            "id": "duckdb_legacy",
            "storage_type": "duckdb_legacy",
            "db": "duckdb_storage/storage.db",
            "base_dir": str(root_path),
            "read_only": False,
        },

        # DuckDb Parquet Storage
        "duckdb_parquet": {
            "id": "duckdb_parquet",
            "storage_type": "duckdb_parquet",
            "base_dir": str(root_path / "duckdb_parquet"),
        },

        # DuckDb S3 Parquet Storage
        "duckdb_s3_parquet": {
            "id": "duckdb_s3_parquet",
            "storage_type": "duckdb_s3_parquet",
            "bucket_url": f"s3:/{root_path}/duckdb-s3-parquet",
            "endpoint_url": f"http://{localstack_host}:4566/",
        },

        # DuckDb Storage
        "duckdb": {
            "id": "duckdb",
            "storage_type": "duckdb",
            "db": "duckdb2_storage/storage2.db",
            "base_dir": str(root_path),
        },

        # DuckDb S3 Storage
        "duckdb_s3": {
            "id": "duckdb_s3",
            "storage_type": "duckdb_s3",
            "db": "storage_s3.db",
            "bucket_url": f"s3:/{root_path}/duckdb-s3",
            "endpoint_url": f"http://{localstack_host}:4566/",
        },
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
            raise ValueError(
                f"unsupported genotype storage type: {storage_type}")
        storage_factories[storage_type] = factory
    return storage_factories


def _populate_default_genotype_storage_factories(
) -> dict[str, Callable[[pathlib.Path], GenotypeStorage]]:
    default_storage_configs = _default_genotype_storage_configs(
        pathlib.Path.cwd())
    storage_factories = {}
    for storage_type in default_storage_configs:
        storage_factories[storage_type] = \
            _default_storage_factory(storage_type)
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
            assert storage_types is not None
            selected_storages = _select_storage_factories_by_type(
                cast(list[str], storage_types))
            if not selected_storages:
                raise ValueError(
                    f"unsupported genotype storage type(s): {storage_types}")
            GENOTYPE_STORAGE_FACTORIES = selected_storages

        elif storage_config_filename:
            import yaml  # pylint: disable=import-outside-toplevel
            assert storage_config_filename is not None
            storage_config = yaml.safe_load(
                pathlib.Path(cast(str, storage_config_filename)).read_text())
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
    if "genotype_storage_factory" in metafunc.fixturenames:
        _generate_genotype_storage_fixtures(metafunc)
    if "grr_scheme" in metafunc.fixturenames:
        _generate_grr_schemes_fixtures(metafunc)


def _generate_genotype_storage_fixtures(metafunc: pytest.Metafunc) -> None:
    assert GENOTYPE_STORAGE_FACTORIES
    storage_factories = GENOTYPE_STORAGE_FACTORIES

    all_storage_types = {
        "inmemory",
        "duckdb_legacy",
        "duckdb_parquet",
        "duckdb_s3_parquet",
        "duckdb",
        "duckdb_s3",
        "impala",
        "impala2",
        "gcp",
        "parquet",
    }
    schema2_storage_types = {
        "duckdb_legacy",
        "duckdb_parquet",
        "duckdb_s3_parquet",
        "duckdb",
        "duckdb_s3",
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

    s3_enabled = False
    if metafunc.config.getoption("enable_s3"):
        s3_enabled = True

    if not s3_enabled:
        if "duckdb_s3_parquet" in storage_factories:
            del storage_factories["duckdb_s3_parquet"]
        if "duckdb_s3" in storage_factories:
            del storage_factories["duckdb_s3"]

    metafunc.parametrize(
        "genotype_storage_factory",
        storage_factories.values(),
        ids=storage_factories.keys(),
        scope="session")


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


@pytest.fixture
def context_fixture(
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> GenomicContext:
    conf_dir = str(tmp_path / "conf")
    mocker.patch("os.environ", {
        "DAE_DB_DIR": conf_dir,
    })
    mocker.patch(
        "dae.genomic_resources.genomic_context._REGISTERED_CONTEXT_PROVIDERS",
        [])
    mocker.patch(
        "dae.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
        [])
    context = get_genomic_context()
    assert context is not None

    return context


@pytest.fixture
def gpf_instance_genomic_context_fixture(
    mocker: pytest_mock.MockerFixture,
) -> Callable[[GPFInstance], GenomicContext]:

    def builder(gpf_instance: GPFInstance) -> GenomicContext:
        mocker.patch(
            "dae.genomic_resources.genomic_context."
            "_REGISTERED_CONTEXT_PROVIDERS",
            [])
        mocker.patch(
            "dae.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
            [])

        context = GPFInstanceGenomicContext(gpf_instance)
        register_context(context)
        assert context is not None

        return context

    return builder
