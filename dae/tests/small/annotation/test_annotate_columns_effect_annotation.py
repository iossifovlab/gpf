# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.annotation.annotate_columns import cli as cli_columns
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    convert_to_tab_separated,
    setup_directories,
)
from dae.testing.t4c8_import import (
    t4c8_grr,
)


@pytest.fixture
def grr_fixture(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    return t4c8_grr(tmp_path / "grr")


@pytest.fixture
def columns_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "work" / "columns.txt"
    setup_directories(
        path,
        convert_to_tab_separated("""
                #chrom   pos   ref  alt
                chr1     10    A    C
                chr1     20    G    A
                chr1     30    T    G
            """),
        )
    return path


def test_annotate_columns_simple(
    tmp_path: pathlib.Path,
    grr_fixture: GenomicResourceRepo,  # noqa: ARG001
    columns_fixture: pathlib.Path,  # noqa: ARG001
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                genome: t4c8_genome
                gene_models: t4c8_genes
            """))

    cli_columns([
        "--grr-directory", str(tmp_path / "grr"),
        "-j", "1",
        "-f",
        "-o", str(tmp_path / "work" / "out.txt"),
        str(tmp_path / "work" / "columns.txt"),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.txt").exists()


def test_annotate_columns_cli_gene_models(
    tmp_path: pathlib.Path,
    grr_fixture: GenomicResourceRepo,  # noqa: ARG001
    columns_fixture: pathlib.Path,  # noqa: ARG001
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                genome: t4c8_genome
            """))

    cli_columns([
        "--grr-directory", str(tmp_path / "grr"),
        "-j", "1",
        "-f",
        "-G", "t4c8_genes",
        "-o", str(tmp_path / "work" / "out.txt"),
        str(tmp_path / "work" / "columns.txt"),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.txt").exists()
