# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
    parse_gr_id_version_token,
    parse_resource_id_version,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    convert_to_tab_separated,
    setup_directories,
)


@pytest.mark.parametrize(
    "token,gr_id,version", [
        ("gene_models(1.0)", "gene_models", (1, 0)),
        ("gene_models(0)", "gene_models", (0,)),
        ("gene_models", "gene_models", (0,)),
    ],
)
def test_parse_gr_id_version_token(
        token: str,
        gr_id: str,
        version: tuple[int, int],
) -> None:
    parsed_gr_id, parsed_version = parse_gr_id_version_token(token)
    assert parsed_gr_id == gr_id
    assert parsed_version == version


@pytest.mark.parametrize(
    "token,resource_id,version", [
        ("gene_models(1.0)", "gene_models", (1, 0)),
        ("gene_models(0)", "gene_models", (0,)),
        ("gene_models", "gene_models", None),
    ],
)
def test_parse_resource_id_version(
        token: str,
        resource_id: str,
        version: tuple[int, ...] | None,
) -> None:
    parsed_resource_id, parsed_version = parse_resource_id_version(token)
    assert parsed_resource_id == resource_id
    assert parsed_version == version


@pytest.fixture
def grr_fixture(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path / "test_local_grr"

    setup_directories(
        root_path,
        {
            "one": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_one
                          type: float
                          name: score
                """),
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  score
                    chr1   4          0.01
                    chr1   54         0.02
                """),
            },
            "one(1.0)": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_one
                          type: float
                          name: score
                """),
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  score
                    chr1   4          0.11
                    chr1   54         0.12
                """),
            },
            "one(1.1)": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_one
                          type: float
                          name: score
                """),
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  score
                    chr1   4          0.11
                    chr1   54         0.12
                """),
            },
        },
    )
    return build_genomic_resource_repository({
        "id": "test_local",
        "type": "directory",
        "directory": str(root_path),
    })


@pytest.mark.parametrize(
    "resource_id_version,expected_version", [
        ("one(1.0)", (1, 0)),
        ("one(1.1)", (1, 1)),
        ("one(0)", (0,)),
        ("one", (1, 1)),
    ],
)
def test_find_resource_with_version(
    grr_fixture: GenomicResourceRepo,
    resource_id_version: str,
    expected_version: tuple[int, int],
) -> None:
    resource = grr_fixture.find_resource(resource_id_version)
    assert resource is not None
    assert resource.resource_id == "one"
    assert resource.version == expected_version
