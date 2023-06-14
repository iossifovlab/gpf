# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.testing import convert_to_tab_separated, setup_directories, \
    setup_genome, setup_denovo
# from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.annotation.annotate_columns import cli as cli_columns


def get_file_content_as_string(file):
    with open(file, "rt", encoding="utf8") as infile:
        return "".join(infile.readlines())


@pytest.fixture
def annotate_directory_fixture(tmp_path):
    setup_directories(
        tmp_path,
        {
            "annotation.yaml": """
                - position_score: one
            """,
            "grr.yaml": f"""
                id: mm
                type: dir
                directory: "{tmp_path}/grr"
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
    setup_denovo(tmp_path / "grr" / "one" / "data.txt", one_content)
    setup_genome(
        tmp_path / "grr" / "foobar_genome" / "chrAll.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )


def test_basic_setup(tmp_path, annotate_directory_fixture, capsys):
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

    setup_directories(tmp_path, {
        "in.txt": in_content,
    })
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    annotation_file = tmp_path / "annotation.yaml"
    grr_file = tmp_path / "grr.yaml"

    # When
    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "--ref", "foobar_genome"
        ]
    ])

    # Then
    out_file_content = get_file_content_as_string(out_file)
    assert out_file_content == out_expected_content
