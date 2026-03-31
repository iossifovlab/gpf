import pathlib
import textwrap

from dae.annotation.annotate_columns import cli
from dae.genomic_resources.testing import setup_tabix


def test_annotate_columns_rerun(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        #chrom   pos
        chr1      3
        chr1      4
        chr1      53
        chr1      54

    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=0, start_col=1, end_col=1)

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--region-size", 5,
            "-j", 1,
        ]
    ])

    assert out_file.is_file()

    out_file.unlink()
    assert not out_file.exists()

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--region-size", 5,
            "-j", 1,
        ]
    ])
    assert out_file.exists()
    assert out_file.is_file()
