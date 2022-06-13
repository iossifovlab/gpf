# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import os

from dae.tools.grr_cache_repo import cli_cache_repo


def test_cli_cache_instance(mocker, fixture_path, temp_cache_dir):
    definition = {
        "id": "local",
        "type": "directory",
        "directory": fixture_path("repo"),
        "cache_dir": temp_cache_dir
    }
    mocked = mocker.patch(
        "dae.tools.grr_cache_repo.load_definition_file")
    mocked.return_value = definition

    cli_cache_repo([
        "--definition",
        "blank",
        "--instance",
        fixture_path("gpf_instance.yaml")
    ])

    paths = [
        ("genomes", "mock"),
        ("gene_models", "mock"),
        ("liftover", "mock"),
        ("scores", "mock1"),
        ("scores", "mock2"),
    ]
    for path in paths:
        full_path = os.path.join(
            temp_cache_dir,
            "local",
            *path,
            "genomic_resource.yaml"
        )
        assert os.path.exists(full_path)

    assert not os.path.exists(os.path.join(
        temp_cache_dir,
        "local",
        "scores",
        "mock_extra",
        "genomic_resource.yaml"
    ))


def test_cli_cache_annotation(mocker, fixture_path, temp_cache_dir):
    definition = {
        "id": "local",
        "type": "directory",
        "directory": fixture_path("repo"),
        "cache_dir": temp_cache_dir
    }
    mocked = mocker.patch(
        "dae.tools.grr_cache_repo.load_definition_file")
    mocked.return_value = definition

    cli_cache_repo([
        "--definition",
        "blank",
        "--annotation",
        fixture_path("annotation.yaml")
    ])

    paths = [
        ("genomes", "mock"),
        ("liftover", "mock"),
        ("scores", "mock1"),
        ("scores", "mock2"),
    ]
    for path in paths:
        full_path = os.path.join(
            temp_cache_dir,
            "local",
            *path,
            "genomic_resource.yaml"
        )
        assert os.path.exists(full_path)

    assert not os.path.exists(os.path.join(
        temp_cache_dir,
        "local",
        "gene_models",
        "mock",
        "genomic_resource.yaml"
    ))
    assert not os.path.exists(os.path.join(
        temp_cache_dir,
        "local",
        "scores",
        "mock_extra",
        "genomic_resource.yaml"
    ))
