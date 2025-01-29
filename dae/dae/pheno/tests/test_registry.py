# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from unittest.mock import MagicMock

import pytest
import pytest_mock

from dae.pheno.pheno_data import PhenotypeGroup, PhenotypeStudy
from dae.pheno.registry import PhenoRegistry
from dae.pheno.storage import PhenotypeStorage, PhenotypeStorageRegistry


@pytest.fixture
def fake_pheno_storage(fake_pheno_db_dir) -> PhenotypeStorage:
    storage_config = {"id": "fake_storage", "base_dir": fake_pheno_db_dir}
    return PhenotypeStorage.from_config(storage_config)


@pytest.fixture
def fake_pheno_storage_registry(
    fake_pheno_storage,
) -> PhenotypeStorageRegistry:
    registry = PhenotypeStorageRegistry()
    registry.register_default_storage(fake_pheno_storage)
    return registry


@pytest.fixture
def mock_classes(
    mocker: pytest_mock.MockerFixture,
) -> tuple[MagicMock, MagicMock]:
    a, b = mocker.spy(PhenotypeStudy, "__init__"), \
           mocker.spy(PhenotypeGroup, "__init__")
    return a, b


@pytest.fixture
def pheno_study_configs() -> dict[str, dict]:
    return {
        "fake": {
            "name": "fake",
            "type": "study",
            "phenotype_storage": {
                "id": "fake_storage",
                "dbfile": "main_fake/fake.db",
            },
        },
        "fake_i1": {
            "name": "fake_i1",
            "type": "study",
            "phenotype_storage": {
                "id": "fake_storage",
                "dbfile": "fake_i1/fake_i1.db",
            },
        },
        "fake2": {
            "name": "fake2",
            "type": "study",
            "phenotype_storage": {
                "id": "fake_storage",
                "dbfile": "fake2/fake2.db",
            },
        },
        "group": {
            "name": "group",
            "type": "group",
            "children": ["fake", "fake2"],
        },
    }


@pytest.fixture
def empty_registry(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
) -> PhenoRegistry:
    return PhenoRegistry(fake_pheno_storage_registry)


@pytest.fixture
def full_registry(
    empty_registry: PhenoRegistry,
    pheno_study_configs: dict[str, dict],
) -> PhenoRegistry:
    empty_registry.register_study_config(pheno_study_configs["fake"])
    empty_registry.register_study_config(pheno_study_configs["fake2"])
    empty_registry.register_study_config(pheno_study_configs["fake_i1"])
    empty_registry.register_study_config(pheno_study_configs["group"])
    return empty_registry


def test_empty_registry_init(empty_registry: PhenoRegistry) -> None:
    assert empty_registry is not None
    assert empty_registry._storage_registry is not None


def test_register_fake(
    empty_registry: PhenoRegistry,
    pheno_study_configs: dict[str, dict],
) -> None:
    empty_registry.register_study_config(pheno_study_configs["fake"])
    assert len(empty_registry._study_configs) == 1
    assert len(empty_registry._cache) == 0


def test_register_and_get_fake(
    empty_registry: PhenoRegistry,
    pheno_study_configs: dict[str, dict],
) -> None:
    empty_registry.register_study_config(pheno_study_configs["fake"])

    study = empty_registry.get_phenotype_data("fake")
    assert study is not None
    assert isinstance(study, PhenotypeStudy)


def test_try_to_load_group_with_unregistered_children(
    empty_registry: PhenoRegistry,
    pheno_study_configs: dict[str, dict],
) -> None:
    error_msg = (
        "Cannot load group group; the following child studies "
        "{'fake', 'fake2'} "
        "are not registered"
    )
    empty_registry.register_study_config(pheno_study_configs["group"])
    with pytest.raises(ValueError, match=error_msg):
        empty_registry.get_phenotype_data("group")


def test_load_group(
    empty_registry: PhenoRegistry,
    pheno_study_configs: dict[str, dict],
) -> None:
    empty_registry.register_study_config(pheno_study_configs["fake"])
    empty_registry.register_study_config(pheno_study_configs["fake2"])
    empty_registry.register_study_config(pheno_study_configs["group"])
    group = empty_registry.get_phenotype_data("group")
    assert group is not None
    assert isinstance(group, PhenotypeGroup)
    assert len(group.children) == 2

    assert {child.pheno_id for child in group.children} == {"fake", "fake2"}


def test_get_all_phenotype_data(full_registry) -> None:
    all_data = full_registry.get_all_phenotype_data()
    assert len(all_data) == 4
    assert set(full_registry.get_phenotype_data_ids()) == {
        "fake", "fake2", "fake_i1", "group",
    }


def test_load_study_called(
    empty_registry: PhenoRegistry,
    pheno_study_configs: dict[str, dict],
    mock_classes: tuple[MagicMock, MagicMock],
) -> None:
    study_mock, group_mock = mock_classes

    empty_registry.register_study_config(pheno_study_configs["fake"])
    empty_registry.get_phenotype_data("fake")

    assert study_mock.call_count == 1
    assert group_mock.call_count == 0


def test_load_group_called(
    empty_registry: PhenoRegistry,
    pheno_study_configs: dict[str, dict],
    mock_classes: tuple[MagicMock, MagicMock],
) -> None:
    study_mock, group_mock = mock_classes

    empty_registry.register_study_config(pheno_study_configs["fake"])
    empty_registry.register_study_config(pheno_study_configs["fake2"])
    empty_registry.register_study_config(pheno_study_configs["group"])
    empty_registry.get_phenotype_data("group")

    assert study_mock.call_count == 2
    assert group_mock.call_count == 1
