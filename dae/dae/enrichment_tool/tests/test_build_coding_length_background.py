# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import polars as pl
import pytest

from dae.enrichment_tool.build_coding_length_enrichment_background import cli
from dae.genomic_resources.testing import setup_directories
from dae.testing.t4c8_import import t4c8_genes


@pytest.fixture()
def grr_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    t4c8_genes(tmp_path / "grr")
    setup_directories(tmp_path, {
        "grr_definition.yaml": textwrap.dedent(f"""
        id: t4c8_genes_testing
        type: dir
        directory: {tmp_path / "grr"}
        """),
    })

    return tmp_path / "grr_definition.yaml"


def test_build_coding_length_background(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
) -> None:
    assert grr_fixture is not None

    output = tmp_path / "coding_len_background.tsv"

    cli([
        "--grr", str(grr_fixture),
        "-o", str(output),
        "t4c8_genes",
    ])

    assert output.exists()
    assert output.is_file()

    df = pl.read_csv(str(output), separator="\t")
    assert df.shape == (2, 2)
    assert df["gene"].to_list() == ["T4", "C8"]
    assert df["gene_weight"].to_list() == [44, 45]
