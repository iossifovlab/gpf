# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Optional, Any
from dae.genotype_storage.genotype_storage_registry import \
    GenotypeStorageRegistry


def default_genotype_storage_configs(root_path):
    return [
        # Impala Schema 1
        {
            "id": "impala",
            "storage_type": "impala",
            "hdfs": {
                "base_dir": "/tmp/genotype_impala_data",
                "host": "localhost",
                "port": 8020,
                "replication": 1,
            },
            "impala": {
                "db": "genotype_impala_db",
                "hosts": [
                    "localhost",
                ],
                "port": 21050,
                "pool_size": 1,
            }
        },

        # Impala Schema 2
        {
            "id": "impala2",
            "storage_type": "impala2",
            "hdfs": {
                "base_dir": "/tmp/genotype_impala2_data",
                "host": "localhost",
                "port": 8020,
                "replication": 1,
            },
            "impala": {
                "db": "genotype_impala2_db",
                "hosts": [
                    "localhost",
                ],
                "port": 21050,
                "pool_size": 1,
            }
        },

        # Filesystem InMemory
        {
            "id": "inmemory",
            "storage_type": "inmemory",
            "dir": f"{root_path}/genotype_filesystem_data"
        }
    ]


GENOTYPE_STORAGE_REGISTRY = GenotypeStorageRegistry()
GENOTYPE_STORAGES: Optional[dict[str, Any]] = None


def _select_storages_by_type(storage_types):
    storages = {}
    for storage_id in GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        storage = GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(storage_id)
        if storage.get_storage_type() in storage_types:
            storages[storage_id] = storage
    return storages


def _select_storages_by_ids(storage_ids):
    storages = {}
    for storage_id in GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        if storage_id in storage_ids:
            storages[storage_id] = \
                GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(storage_id)
    return storages


def _populate_storages_from_registry():
    storages = {}
    for storage_id in GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        storages[storage_id] = \
            GENOTYPE_STORAGE_REGISTRY.get_genotype_storage(storage_id)
    return storages


def _populate_default_genotype_storages(root_path):
    if not GENOTYPE_STORAGE_REGISTRY.get_all_genotype_storage_ids():
        for storage_config in default_genotype_storage_configs(root_path):
            GENOTYPE_STORAGE_REGISTRY\
                .register_storage_config(storage_config)
    return GENOTYPE_STORAGE_REGISTRY


def pytest_addoption(parser):
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


def pytest_sessionstart(session):
    global GENOTYPE_STORAGES  # pylint: disable=global-statement
    if not GENOTYPE_STORAGES:
        # pylint: disable=protected-access
        root_path = session\
            .config\
            ._tmp_path_factory.mktemp("genotype_storage")
        _populate_default_genotype_storages(root_path)

        storage_types = session.config.getoption("storage_types")
        storage_ids = session.config.getoption("storage_ids")
        storage_config_filename = \
            session.config.getoption("storage_config")

        if storage_types:
            assert not storage_ids
            assert not storage_config_filename
            GENOTYPE_STORAGES = _select_storages_by_type(storage_types)
        elif storage_ids:
            assert not storage_config_filename
            GENOTYPE_STORAGES = _select_storages_by_ids(storage_ids)

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


def pytest_generate_tests(metafunc):
    if "genotype_storage" in metafunc.fixturenames:

        assert GENOTYPE_STORAGES is not None
        storages = GENOTYPE_STORAGES

        if hasattr(metafunc, "function"):
            marked_types = set()
            for mark in getattr(metafunc.function, "pytestmark", []):
                marked_types.add(mark.name)
            result = {}
            for storage_id, storage in GENOTYPE_STORAGES.items():
                if storage.get_storage_type() in marked_types:
                    result[storage_id] = storage
            if result:
                storages = result

        metafunc.parametrize(
            "genotype_storage",
            storages.values(),
            ids=storages.keys(),
            scope="module")
