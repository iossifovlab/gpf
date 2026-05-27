# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import os
import pathlib
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
import pytest_mock
from gain.genomic_resources.cli_cache_repo import cli_cache_repo


@pytest.mark.parametrize(
    "instance_conf_name",
    ["gpf_instance.yaml",
     "gpf_instance_embedded_annotation.yaml"],
)
def test_cli_cache_instance(
    mocker: pytest_mock.MockerFixture,
    fixture_path: Callable[[str], str],
    instance_conf_name: str,
    tmp_path: pathlib.Path,
) -> None:
    definition: dict[str, Any] = {
        "id": "local",
        "type": "directory",
        "directory": fixture_path("repo"),
        "cache_dir": tmp_path,
    }
    mocked: MagicMock = mocker.patch(
        "gain.genomic_resources.repository_factory.load_definition_file")
    mocked.return_value = definition

    cli_cache_repo([
        "--grr",
        "blank",
        "-j", "1",
        "--instance",
        fixture_path(instance_conf_name),
    ])

    paths: list[tuple[str, str]] = [
        ("genomes", "mock"),
        ("genomes", "mock0"),
        ("gene_models", "mock"),
        ("liftover", "mock"),
        ("scores", "mock1"),
        ("scores", "mock2"),
    ]
    for path in paths:
        full_path: str = os.path.join(
            tmp_path,
            "local",
            *path,
            "genomic_resource.yaml",
        )
        assert os.path.exists(full_path), full_path

    assert not os.path.exists(os.path.join(
        tmp_path,
        "local",
        "scores",
        "mock_extra",
        "genomic_resource.yaml",
    ))
