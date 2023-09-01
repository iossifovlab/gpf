# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pathlib

import pytest

from dae.testing import convert_to_tab_separated, setup_directories, \
    setup_genome, setup_denovo
from dae.annotation.annotate_columns import cli as cli_columns


def get_file_content_as_string(file: str) -> str:
    with open(file, "rt", encoding="utf8") as infile:
        return "".join(infile.readlines())


@pytest.fixture
def annotate_directory_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    root_path = tmp_path / "annotate_columns_cshl"
    setup_directories(
        root_path,
        {
            "annotation.yaml": """
                - position_score: one
            """,
            "grr.yaml": f"""
                id: mm
                type: dir
                directory: "{root_path}/grr"
            """,
            "grr": {
                "one": {
                    "genomic_resource.yaml": """
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          name: s1
                    """
                },
                "foobar_genome": {
                    "genomic_resource.yaml": """
                        type: genome
                        filename: chrAll.fa
                        chrom_prefix: "chr"
                    """
                }
            }
        }
    )
    one_content = textwrap.dedent("""
        chrom  pos_begin  s1
        chrA   10         0.01
        chrA   11         0.2
    """)
    setup_denovo(root_path / "grr" / "one" / "data.txt", one_content)
    setup_genome(
        root_path / "grr" / "foobar_genome" / "chrAll.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    return root_path


def test_annotate_columns_cshl_basic_setup(
        annotate_directory_fixture: pathlib.Path,
        capsys: pytest.CaptureFixture) -> None:
    # Given
    in_content = convert_to_tab_separated("""
        location  variant
        chrA:10   sub(A->C)
        chrA:11   sub(A->T)
    """)
    out_expected_content = convert_to_tab_separated("""
        location  variant   score
        chrA:10   sub(A->C) 0.01
        chrA:11   sub(A->T) 0.2
    """)

    root_path = annotate_directory_fixture

    setup_directories(root_path, {
        "in.txt": in_content,
    })
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    # When
    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "--ref", "foobar_genome",
            "-j", 1,
            "-w", work_dir,
        ]
    ])

    # Then
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content
