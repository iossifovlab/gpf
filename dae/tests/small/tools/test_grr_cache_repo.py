# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import os
import pathlib

import pytest
from dae.tools.grr_cache_repo import cli_cache_repo


@pytest.mark.parametrize(
    "instance_conf_name",
    ["gpf_instance.yaml",
     "gpf_instance_embedded_annotation.yaml"],
)
def test_cli_cache_instance(
    mocker,
    fixture_path,
    instance_conf_name,
    tmp_path: pathlib.Path,
):
    definition = {
        "id": "local",
        "type": "directory",
        "directory": fixture_path("repo"),
        "cache_dir": tmp_path,
    }
    mocked = mocker.patch(
        "dae.tools.grr_cache_repo.load_definition_file")
    mocked.return_value = definition

    cli_cache_repo([
        "--grr",
        "blank",
        "-j", "1",
        "--instance",
        fixture_path(instance_conf_name),
    ])

    paths = [
        ("genomes", "mock"),
        ("genomes", "mock0"),
        ("gene_models", "mock"),
        ("liftover", "mock"),
        ("scores", "mock1"),
        ("scores", "mock2"),
    ]
    for path in paths:
        full_path = os.path.join(
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


def test_cli_cache_annotation(
        mocker,
        fixture_path,
        tmp_path: pathlib.Path,
) -> None:
    definition = {
        "id": "local",
        "type": "directory",
        "directory": fixture_path("repo"),
        "cache_dir": tmp_path,
    }
    mocked = mocker.patch(
        "dae.tools.grr_cache_repo.load_definition_file")
    mocked.return_value = definition

    cli_cache_repo([
        "--grr",
        "blank",
        "-j", "1",
        "--annotation",
        fixture_path("annotation.yaml"),
    ])

    paths = [
        ("genomes", "mock"),
        ("liftover", "mock"),
        ("scores", "mock1"),
        ("scores", "mock2"),
    ]
    for path in paths:
        full_path = os.path.join(
            tmp_path,
            "local",
            *path,
            "genomic_resource.yaml",
        )
        assert os.path.exists(full_path)

    assert not os.path.exists(os.path.join(
        tmp_path,
        "local",
        "gene_models",
        "mock",
        "genomic_resource.yaml",
    ))
    assert not os.path.exists(os.path.join(
        tmp_path,
        "local",
        "scores",
        "mock_extra",
        "genomic_resource.yaml",
    ))
