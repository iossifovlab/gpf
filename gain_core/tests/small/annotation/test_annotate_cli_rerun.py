import pathlib
import textwrap

from gain.annotation.annotate_columns import cli as cli_columns
from gain.annotation.annotate_vcf import cli as cli_vcf
from gain.genomic_resources.testing import setup_tabix, setup_vcf


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

    cli_columns([
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

    cli_columns([
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


def test_annotate_vcf_rerun(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    vcf_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT s1
        chr1   3   .  C   T   .    .      .    GT     0/1
        chr1   4   .  C   A   .    .      .    GT     0/1
        chr1   53  .  C   G   .    .      .    GT     0/1
        chr1   54  .  C   T   .    .      .    GT     0/1
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, vcf_content)

    cli_vcf([
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

    cli_vcf([
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
