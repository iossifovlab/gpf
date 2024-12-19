# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from unittest.mock import MagicMock

import pytest
import pytest_mock

from dae.pheno.pheno_data import (
    PhenotypeGroup,
    PhenotypeStudy,
    load_phenotype_data,
)


@pytest.fixture
def mock_sort(mocker: pytest_mock.MockerFixture) -> MagicMock:
    return mocker.patch(
        "dae.pheno.pheno_data._sort_group_children", autospec=True,
    )

@pytest.fixture
def mock_classes(
    mocker: pytest_mock.MockerFixture,
) -> tuple[MagicMock, MagicMock]:
    return mocker.patch("dae.pheno.pheno_data.PhenotypeStudy", autospec=True), \
           mocker.patch("dae.pheno.pheno_data.PhenotypeGroup", autospec=True)


def test_load_phenotype_data_study(
    mock_classes: tuple[MagicMock, MagicMock],
    mock_sort: MagicMock,  # noqa: ARG001
) -> None:
    study_mock, _ = mock_classes
    config = {
        "name": "test",
        "dbfile": "test.db",
        "type": "study",
    }
    result = load_phenotype_data(config)
    assert isinstance(result, PhenotypeStudy)
    assert study_mock.call_count == 1


def test_load_phenotype_data_group(
    mock_classes: tuple[MagicMock, MagicMock],
) -> None:
    study_mock, group_mock = mock_classes
    config = {
        "name": "test_group",
        "type": "group",
        "children": ["test_child_1", "test_child_2"],
    }
    children_configs = [
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
    result = load_phenotype_data(config, children_configs)
    assert isinstance(result, PhenotypeGroup)
    assert group_mock.call_count == 2
    assert study_mock.call_count == 2


def test_load_phenotype_data_group_no_children(
    mock_classes: tuple[MagicMock, MagicMock],  # noqa: ARG001
) -> None:
    config = {
        "name": "test",
        "type": "group",
    }
    with pytest.raises(ValueError, match="without extra configs"):
        load_phenotype_data(config)


def test_load_phenotype_data_invalid(
    mock_classes: tuple[MagicMock, MagicMock],  # noqa: ARG001
) -> None:
    config = {
        "name": "test",
        "type": "INVALIDTYPE",
    }
    with pytest.raises(ValueError, match="Unknown config type"):
        load_phenotype_data(config)
