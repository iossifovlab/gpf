# pylint: disable=W0621,C0114,C0116,W0212,W0613
import shutil
import tempfile
import pytest
import textwrap
import pandas as pd
from pathlib import Path

from dae.genomic_resources.testing import setup_directories
from demo_annotator.annotate_length import annotate_length_cli


@pytest.fixture()
def sample_input_output() -> tuple[str, str]:
    test_files_dirname = tempfile.mkdtemp(
        prefix="annotate_length", suffix="_test"
    )

    setup_directories(test_files_dirname, {
        "input.tsv": textwrap.dedent("""
            VCFAllele(chr1,10,C,T)
            VCFAllele(chr1,11,G,C)
            VCFAllele(chr1,23,T,C)
            VCFAllele(chr1,34,C,T)
            VCFAllele(chr2,11,A,G)
            VCFAllele(chr2,15,C,A)
            VCFAllele(chr2,20,C,T)
            VCFAllele(chr2,40,T,C)
            VCFAllele(chr3,30,T,C)
        """)
    })

    yield (
        Path(test_files_dirname, "input.tsv").as_posix(),
        Path(test_files_dirname, "output.tsv").as_posix(),
    )

    shutil.rmtree(test_files_dirname)


def test_annotate_length_cli(sample_input_output):
    input_file, output_file = sample_input_output

    annotate_length_cli([input_file, output_file])

    df = pd.read_csv(output_file, delimiter="\t", header=None)
    assert len(df) == 9
    assert df[1][0] == 0
    assert df[1][1] == 0
    assert df[1][2] == 0
    assert df[1][3] == 0
    assert df[1][4] == 0
    assert df[1][5] == 0
    assert df[1][6] == 0
    assert df[1][7] == 0
    assert df[1][8] == 0
