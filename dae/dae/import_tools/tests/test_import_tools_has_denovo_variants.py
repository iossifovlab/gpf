# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Any
import pytest

from dae.import_tools.import_tools import ImportProject
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing.alla_import import alla_gpf


@pytest.fixture
def gpf_fixture(tmp_path: pathlib.Path) -> GPFInstance:
    return alla_gpf(tmp_path)


def test_import_project_denovo_loader(
        tmp_path: pathlib.Path,
        gpf_fixture: GPFInstance) -> None:

    import_config: dict[str, Any] = {
        "input": {
            "denovo": {
                "files": [
                    "denovo.tsv"
                ]
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project is not None
    assert project.has_denovo_variants()


@pytest.mark.parametrize("denovo_mode, has_denovo", [
    ("denovo", True),
    ("possible_denovo", False),
    ("ignore", False),
])
def test_import_project_vcf_loader_denovo_mode(
        denovo_mode: str,
        has_denovo: bool,
        tmp_path: pathlib.Path,
        gpf_fixture: GPFInstance) -> None:

    import_config: dict[str, Any] = {
        "input": {
            "vcf": {
                "files": [
                    "denovo.vcf"
                ],
                "denovo_mode": denovo_mode
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project is not None
    assert project.has_denovo_variants() == has_denovo


@pytest.mark.parametrize("denovo_mode", [
    "denovo",
    "possible_denovo",
    "ignore",
])
def test_import_project_mixed_denovo_and_vcf_loader_denovo_mode(
        denovo_mode: str,
        tmp_path: pathlib.Path,
        gpf_fixture: GPFInstance) -> None:

    import_config: dict[str, Any] = {
        "input": {
            "denovo": {
                "files": [
                    "denovo.tsv"
                ]
            },
            "vcf": {
                "files": [
                    "denovo.vcf"
                ],
                "denovo_mode": denovo_mode
            },
        },
    }
    project = ImportProject.build_from_config(
        import_config, gpf_instance=gpf_fixture)
    assert project is not None
    assert project.has_denovo_variants()
