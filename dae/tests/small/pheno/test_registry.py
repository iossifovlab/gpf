# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib
from unittest.mock import MagicMock

import pytest
import pytest_mock
from dae.pheno.pheno_data import PhenotypeGroup, PhenotypeStudy
from dae.pheno.registry import PhenoRegistry
from dae.pheno.storage import PhenotypeStorage, PhenotypeStorageRegistry
from dae.studies.variants_db import DEFAULT_STUDY_CONFIG


@pytest.fixture
def fake_pheno_storage(fake_pheno_db_dir: pathlib.Path) -> PhenotypeStorage:
    storage_config = {"id": "fake_storage", "base_dir": fake_pheno_db_dir}
    return PhenotypeStorage.from_config(storage_config)


@pytest.fixture
def fake_pheno_storage_registry(
    fake_pheno_storage: PhenotypeStorage,
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
def pheno_study_configs(
    tmp_path: pathlib.Path,
    fake_pheno_db_dir: pathlib.Path,
) -> pathlib.Path:
    conf_dir = pathlib.Path(tmp_path / "pheno_confs")
    conf_dir.mkdir()

    fake = f"""
        id: fake
        enabled: true
        name: Fake Study
        type: study
        dbfile: {fake_pheno_db_dir / "fake" / "fake.db"}
    """
    fake_i1 = f"""
        id: fake_i1
        enabled: True
        name: Fake Study 1
        type: study
        dbfile: {fake_pheno_db_dir / "fake_i1" / "fake_i1.db"}
    """
    fake2 = f"""
        id: fake2
        enabled: True
        name: Fake Study 2
        type: study
        dbfile: {fake_pheno_db_dir / "fake2" / "fake2.db"}
    """
    fake3 = f"""
        id: fake3
        enabled: False
        name: Fake Study 3
        type: study
        dbfile: {fake_pheno_db_dir / "fake" / "fake.db"}
    """
    group = """
        id: group
        enabled: True
        name: Fake Group
        type: group
        children:
          - fake
          - fake2
    """
    pathlib.Path(conf_dir / "fake.yaml").write_text(fake)
    pathlib.Path(conf_dir / "fake_i1.yaml").write_text(fake_i1)
    pathlib.Path(conf_dir / "fake2.yaml").write_text(fake2)
    pathlib.Path(conf_dir / "fake3.yaml").write_text(fake3)
    pathlib.Path(conf_dir / "group.yaml").write_text(group)

    return conf_dir


@pytest.fixture
def empty_registry(
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
) -> PhenoRegistry:
    return PhenoRegistry(fake_pheno_storage_registry)


@pytest.fixture
def full_registry(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
) -> PhenoRegistry:
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake2.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake_i1.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake3.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "group.yaml"))
    return empty_registry


def test_empty_registry_init(empty_registry: PhenoRegistry) -> None:
    assert empty_registry is not None
    assert empty_registry._storage_registry is not None


def test_register_fake(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
) -> None:
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))
    assert len(empty_registry._study_configs) == 1
    assert len(empty_registry._cache) == 0


def test_register_and_get_fake(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
) -> None:
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))

    study = empty_registry.get_phenotype_data("fake")
    assert study is not None
    assert isinstance(study, PhenotypeStudy)


def test_try_to_load_group_with_unregistered_children(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
) -> None:
    error_msg = (
        "Cannot load group group; the following child studies "
        r"({'fake', 'fake2'}|{'fake2', 'fake'}) "  # regex that matches either
        "are not registered"
    )
    empty_registry._register_study_config(
        str(pheno_study_configs / "group.yaml"))
    with pytest.raises(ValueError, match=error_msg):
        empty_registry.get_phenotype_data("group")


def test_load_group(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
) -> None:
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake2.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "group.yaml"))
    group = empty_registry.get_phenotype_data("group")
    assert group is not None
    assert isinstance(group, PhenotypeGroup)
    assert len(group.children) == 2

    assert {child.pheno_id for child in group.children} == {"fake", "fake2"}


def test_get_all_phenotype_data(full_registry: PhenoRegistry) -> None:
    all_data = full_registry.get_all_phenotype_data()
    assert len(all_data) == 4
    assert set(full_registry.get_phenotype_data_ids()) == {
        "fake", "fake2", "fake_i1", "group",
    }


def test_load_study_called(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
    mock_classes: tuple[MagicMock, MagicMock],
) -> None:
    study_mock, group_mock = mock_classes

    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))
    empty_registry.get_phenotype_data("fake")

    assert study_mock.call_count == 1
    assert group_mock.call_count == 0


def test_load_group_called(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
    mock_classes: tuple[MagicMock, MagicMock],
) -> None:
    study_mock, group_mock = mock_classes

    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake2.yaml"))
    empty_registry._register_study_config(
        str(pheno_study_configs / "group.yaml"))
    empty_registry.get_phenotype_data("group")

    assert study_mock.call_count == 2
    assert group_mock.call_count == 1


def test_disabled_study_not_registered(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
) -> None:
    assert len(empty_registry._study_configs) == 0

    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))
    assert len(empty_registry._study_configs) == 1

    empty_registry._register_study_config(
        str(pheno_study_configs / "fake2.yaml"))
    assert len(empty_registry._study_configs) == 2

    empty_registry._register_study_config(
        str(pheno_study_configs / "fake3.yaml"))
    assert len(empty_registry._study_configs) == 2


def test_default_person_sets_configuration(
    empty_registry: PhenoRegistry,
    pheno_study_configs: pathlib.Path,
) -> None:
    empty_registry._register_study_config(
        str(pheno_study_configs / "fake.yaml"))
    config = empty_registry.get_phenotype_data_config("fake")
    assert config is not None
    assert "person_set_collections" in config
    assert config["person_set_collections"] == \
        DEFAULT_STUDY_CONFIG["person_set_collections"]
