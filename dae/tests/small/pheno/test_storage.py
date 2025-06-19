# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest
from dae.pheno.storage import PhenotypeStorage, PhenotypeStorageRegistry


@pytest.fixture
def fake_pheno_storage(fake_pheno_db_dir) -> PhenotypeStorage:
    storage_config = {"id": "fake_storage", "base_dir": fake_pheno_db_dir}
    return PhenotypeStorage.from_config(storage_config)


@pytest.fixture
def empty_storage_config(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict:
    return {
        "id": "storage1",
        "base_dir": tmp_path_factory.mktemp("storage1"),
    }


@pytest.fixture
def empty_storage(
    empty_storage_config: dict,
) -> PhenotypeStorage:
    return PhenotypeStorage.from_config(empty_storage_config)


@pytest.fixture
def fake_pheno_storage_registry(
    fake_pheno_storage,
) -> PhenotypeStorageRegistry:
    registry = PhenotypeStorageRegistry()
    registry.register_default_storage(fake_pheno_storage)
    return registry


def test_storage_init(
    fake_pheno_storage: PhenotypeStorage,
) -> None:
    assert fake_pheno_storage is not None


def test_storage_in_registry(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
) -> None:
    assert "fake_storage" in fake_pheno_storage_registry
    storage = fake_pheno_storage_registry.get_phenotype_storage("fake_storage")
    assert storage is not None


def test_storage_register_new_storage_by_config(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
    empty_storage_config: dict,
) -> None:
    fake_pheno_storage_registry.register_storage_config(empty_storage_config)

    assert "storage1" in fake_pheno_storage_registry

    assert len(
        fake_pheno_storage_registry.get_all_phenotype_storage_ids()) == 2


def test_storage_register_new_storages_by_section(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
    empty_storage_config: dict,
) -> None:
    configs = [
        {"id": f"storage{idx}", "base_dir": empty_storage_config["base_dir"]}
        for idx in range(1, 6)
    ]
    gpf_config_section = {"default": "storage3", "storages": configs}

    fake_pheno_storage_registry.register_storages_configs(gpf_config_section)

    assert "fake_storage" in fake_pheno_storage_registry
    assert "storage1" in fake_pheno_storage_registry
    assert "storage2" in fake_pheno_storage_registry
    assert "storage3" in fake_pheno_storage_registry
    assert "storage4" in fake_pheno_storage_registry
    assert "storage5" in fake_pheno_storage_registry

    assert len(
        fake_pheno_storage_registry.get_all_phenotype_storage_ids()) == 6

    default_storage = \
        fake_pheno_storage_registry.get_default_phenotype_storage()

    assert default_storage.storage_id == "storage3"


def test_registry_sets_default_storage(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
) -> None:
    default_storage = \
        fake_pheno_storage_registry.get_default_phenotype_storage()

    assert default_storage.storage_id == "fake_storage"


def test_registry_overwrite_default_storage(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
    empty_storage: PhenotypeStorage,
) -> None:
    default_storage = \
        fake_pheno_storage_registry.get_default_phenotype_storage()

    assert default_storage.storage_id == "fake_storage"

    fake_pheno_storage_registry.register_default_storage(empty_storage)

    default_storage = \
        fake_pheno_storage_registry.get_default_phenotype_storage()

    assert default_storage.storage_id == "storage1"


def test_registry_getters(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
    empty_storage: PhenotypeStorage,
) -> None:
    fake_pheno_storage_registry.register_phenotype_storage(empty_storage)

    storage = fake_pheno_storage_registry.get_phenotype_storage("fake_storage")
    assert storage.storage_id == "fake_storage"
    storage = fake_pheno_storage_registry.get_phenotype_storage("storage1")
    assert storage.storage_id == "storage1"

    all_storages = fake_pheno_storage_registry.get_all_phenotype_storages()
    assert len(all_storages) == 2

    assert {storage.storage_id for storage in all_storages} == {
        "fake_storage",
        "storage1",
    }

    assert all_storages[0].storage_id == "fake_storage"
    assert all_storages[1].storage_id == "storage1"
    all_storage_ids = \
        fake_pheno_storage_registry.get_all_phenotype_storage_ids()
    assert set(all_storage_ids) == {
        "fake_storage",
        "storage1",
    }
