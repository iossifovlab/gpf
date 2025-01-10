# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from unittest.mock import MagicMock

import pytest
import pytest_mock

from dae.pheno.pheno_data import (
    PhenotypeGroup,
    PhenotypeStudy,
)
from dae.pheno.registry import PhenoRegistry


@pytest.fixture
def mock_classes(
    mocker: pytest_mock.MockerFixture,
) -> tuple[MagicMock, MagicMock]:
    a, b = mocker.spy(PhenotypeStudy, "__init__"), \
           mocker.spy(PhenotypeGroup, "__init__")
    mocker.patch("dae.pheno.pheno_data.PhenoDb", autospec=True)
    mocker.patch("dae.pheno.registry.PhenotypeStudy._get_measures_df")
    mocker.patch("dae.pheno.registry.PhenotypeStudy._load_instruments")
    return a, b


def test_registry_get_or_load_study(
    mock_classes: tuple[MagicMock, MagicMock],
) -> None:
    study_mock, _ = mock_classes
    config = {
        "name": "test",
        "dbfile": "test.db",
        "type": "study",
    }
    configurations = {"test": config}
    registry = PhenoRegistry()
    result = registry.get_or_load("test", configurations)
    assert isinstance(result, PhenotypeStudy)
    assert study_mock.call_count == 1


def test_registry_get_or_load_group(
    mock_classes: tuple[MagicMock, MagicMock],
) -> None:
    study_mock, group_mock = mock_classes
    all_configs = [
        {
            "name": "test_group",
            "type": "group",
            "children": ["test_child_1", "test_child_2"],
        },
        {
            "name": "test_child_1",
            "dbfile": "test1.db",
            "type": "study",
        },
        {
            "name": "test_child_2",
            "type": "group",
            "children": ["test_child_3"],
        },
        {
            "name": "test_child_3",
            "dbfile": "test3.db",
            "type": "study",
        },
    ]
    configurations = {config["name"]: config for config in all_configs}
    registry = PhenoRegistry()
    result = registry.get_or_load("test_group", configurations)
    assert isinstance(result, PhenotypeGroup)
    assert group_mock.call_count == 2
    assert study_mock.call_count == 2


def test_registry_get_or_load_invalid(
    mock_classes: tuple[MagicMock, MagicMock],  # noqa: ARG001
) -> None:
    configs = {"test": {"name": "test", "type": "INVALIDTYPE"}}
    registry = PhenoRegistry()
    with pytest.raises(ValueError, match="Invalid type"):
        registry.get_or_load("test", configs)
