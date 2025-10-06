# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.annotation.annotate_columns import cli as cli_columns
from dae.annotation.annotate_vcf import cli as cli_vcf
from dae.genomic_resources.testing import (
    convert_to_tab_separated,
    setup_directories,
    setup_vcf,
)
from dae.testing.t4c8_import import (
    t4c8_grr,
)


@pytest.fixture
def grr_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "grr"
    t4c8_grr(path)
    return path


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


@pytest.fixture
def vcf_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    return setup_vcf(
        tmp_path / "work" / "in.vcf",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1
        chr1   10  .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0
        chr1   20  .  G   A   .    .      .    GT     0/0 0/1 0/1 0/0
        chr1   30  .  T   G   .    .      .    GT     1/0 0/0 0/0 0/1
        """)


def test_annotate_columns_simple(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    columns_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                genome: t4c8_genome
                gene_models: t4c8_genes
            """))

    cli_columns([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-o", str(tmp_path / "work" / "out.txt"),
        str(columns_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.txt").exists()


def test_annotate_columns_cli_gene_models(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    columns_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                genome: t4c8_genome
            """))

    cli_columns([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-G", "t4c8_genes",
        "-o", str(tmp_path / "work" / "out.txt"),
        str(columns_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.txt").exists()


def test_annotate_columns_cli_reference_genome(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    columns_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                gene_models: t4c8_genes
            """))

    cli_columns([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-R", "t4c8_genome",
        "-o", str(tmp_path / "work" / "out.txt"),
        str(columns_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.txt").exists()


def test_annotate_columns_cli_gene_models_and_reference_genome(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    columns_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator
            """))

    cli_columns([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-G", "t4c8_genes",
        "-R", "t4c8_genome",
        "-o", str(tmp_path / "work" / "out.txt"),
        str(columns_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.txt").exists()


def test_annotate_columns_simple_effect_annotator_cli_gene_models(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    columns_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - simple_effect_annotator
            """))

    cli_columns([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-G", "t4c8_genes",
        "-o", str(tmp_path / "work" / "out.txt"),
        str(columns_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.txt").exists()


def test_annotate_vcf_simple(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    vcf_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                genome: t4c8_genome
                gene_models: t4c8_genes
            """))

    cli_vcf([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-o", str(tmp_path / "work" / "out.vcf"),
        str(vcf_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.vcf").exists()


def test_annotate_vcf_cli_gene_models(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    vcf_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                genome: t4c8_genome
            """))

    cli_vcf([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-G", "t4c8_genes",
        "-o", str(tmp_path / "work" / "out.vcf"),
        str(vcf_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.vcf").exists()


def test_annotate_vcf_cli_reference_genome(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    vcf_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator:
                gene_models: t4c8_genes
            """))

    cli_vcf([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-R", "t4c8_genome",
        "-o", str(tmp_path / "work" / "out.vcf"),
        str(vcf_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.vcf").exists()


def test_annotate_vcf_cli_gene_models_and_reference_genome(
    tmp_path: pathlib.Path,
    grr_fixture: pathlib.Path,
    vcf_fixture: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "work" / "pipeline.yaml",
        textwrap.dedent("""
            - effect_annotator
            """))

    cli_vcf([
        "--grr-directory", str(grr_fixture),
        "-j", "2",
        "-f",
        "-G", "t4c8_genes",
        "-R", "t4c8_genome",
        "-o", str(tmp_path / "work" / "out.vcf"),
        str(vcf_fixture),
        str(tmp_path / "work" / "pipeline.yaml"),
    ])

    assert (tmp_path / "work" / "out.vcf").exists()
