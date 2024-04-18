# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dae.annotation.annotate_columns import cli as cli_columns
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.testing import convert_to_tab_separated, setup_directories
from dae.testing.foobar_import import foobar_genes, foobar_genome


@pytest.fixture()
def annotate_cnv_fixture(tmp_path: Path) -> Path:
    root_path = tmp_path / "annotate_columns_cnv_pipeline"

    foobar_genome(
        root_path / "grr" / "genome")
    foobar_genes(
        root_path / "grr" / "gene_models")

    setup_directories(
        root_path, {
            "input": {
                "cnv_cshl.tsv": convert_to_tab_separated("""
                    location    variant
                    foo:3-19    cnv+
                    bar:3-19    cnv-
                """),
                "cnv.tsv": convert_to_tab_separated("""
                    chrom  pos_beg  pos_end  cnv_type
                    foo    3        19       cnv+
                    bar    3        19       cnv-
                """),
                "bad_cnv.tsv": convert_to_tab_separated("""
                    chrom  pos_beg  pos_end  cnv_type
                    foo    3        19       bla
                    bar    3        19       haha
                    bla    3        19       cnv+
                """),
            },
            "grr.yaml": textwrap.dedent(f"""
                id: cnv_repo
                type: dir
                directory: "{root_path}/grr"
            """),
            "grr": {
                "genome": {
                    "foobar_genome": {
                        "genomic_resource.yaml": textwrap.dedent("""
                            type: genome
                            filename: chrAll.fa
                        """),
                    },
                },
                "gene_models": {
                    "foobar_genes": {
                        "genomic_resource.yaml": textwrap.dedent("""
                            type: gene_models
                            filename: genes.txt
                            format: refflat
                        """),
                    },
                },
                "one": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          name: s1
                    """),
                    "data.txt": convert_to_tab_separated("""
                        chrom  pos_begin  s1
                        foo    4          0.1
                        foo    18         0.2
                        bar    4          1.1
                        bar    18         1.2
                    """),
                },
                "gene_score1": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: gene_score
                        filename: score.csv
                        scores:
                        - id: gene_score1
                          desc: Test gene score
                          histogram:
                            type: number
                            number_of_bins: 100
                            view_range:
                              min: 0.0
                              max: 56.0
                    """),
                    "score.csv": textwrap.dedent("""
                        gene,gene_score1
                        g1,10.1
                        g2,20.2
                    """),
                },
            },
        },
    )
    return root_path


def test_cnv_cli_columns_basic_setup(
    annotate_cnv_fixture: Path,
) -> None:
    root_path = annotate_cnv_fixture
    grr_path = root_path / "grr.yaml"
    grr = build_genomic_resource_repository(file_name=str(grr_path))
    assert grr is not None

    genome = grr.get_resource("genome/foobar_genome")
    assert genome is not None
    assert genome.get_type() == "genome"
    assert genome.resource_id == "genome/foobar_genome"

    gene_models = grr.get_resource("gene_models/foobar_genes")
    assert gene_models is not None
    assert gene_models.get_type() == "gene_models"
    assert gene_models.resource_id == "gene_models/foobar_genes"


@pytest.mark.parametrize(
    "infile", [
        "cnv_cshl.tsv",
        "cnv.tsv",
    ],
)
def test_cnv_effect_annotation(
    infile: str,
    annotate_cnv_fixture: Path,
) -> None:
    root_path = annotate_cnv_fixture
    setup_directories(root_path, {
        "effect_annotation.yaml": textwrap.dedent("""
        - effect_annotator:
            gene_models: gene_models/foobar_genes
            genome: genome/foobar_genome
            attributes:
            - source: gene_list
            - source: worst_effect
            - source: gene_effects
        """),
    })
    cli_columns([
        str(root_path / "input" / infile),
        str(root_path / "effect_annotation.yaml"),
        "-o", str(root_path / "result.tsv"),
        "-w", str(root_path / "work"),
        "--grr", str(root_path / "grr.yaml"),
        "-R", "genome/foobar_genome",
        "-j", "1",
    ])

    df = pd.read_csv(root_path / "result.tsv", sep="\t")
    assert list(df.worst_effect.values) == ["CNV+", "CNV-"]
    assert list(df.gene_effects.values) == ["g1:CNV+", "g2:CNV-"]
    assert list(df.gene_list.values) == ["['g1']", "['g2']"]


@pytest.mark.parametrize(
    "infile", [
        "cnv_cshl.tsv",
        "cnv.tsv",
    ],
)
def test_cnv_gene_score_annotation(
    infile: str,
    annotate_cnv_fixture: Path,
) -> None:
    root_path = annotate_cnv_fixture
    setup_directories(root_path, {
        "gene_score_annotation.yaml": textwrap.dedent("""
        - effect_annotator:
            gene_models: gene_models/foobar_genes
            genome: genome/foobar_genome
        - gene_score_annotator:
            resource_id: gene_score1
            input_gene_list: gene_list
            attributes:
            - source: gene_score1
              gene_aggregator: max
        """),
    })
    cli_columns([
        str(root_path / "input" / infile),
        str(root_path / "gene_score_annotation.yaml"),
        "-o", str(root_path / "result.tsv"),
        "-w", str(root_path / "work"),
        "--grr", str(root_path / "grr.yaml"),
        "-R", "genome/foobar_genome",
        "-j", "1",
    ])

    df = pd.read_csv(root_path / "result.tsv", sep="\t")
    assert list(df.worst_effect.values) == ["CNV+", "CNV-"]
    assert list(df.gene_score1.values) == [10.1, 20.2]


@pytest.mark.parametrize(
    "infile", [
        "bad_cnv.tsv",
    ],
)
def test_bad_cnv_effect_annotation(
    infile: str,
    annotate_cnv_fixture: Path,
) -> None:
    root_path = annotate_cnv_fixture
    setup_directories(root_path, {
        "effect_annotation.yaml": textwrap.dedent("""
        - effect_annotator:
            gene_models: gene_models/foobar_genes
            genome: genome/foobar_genome
            attributes:
            - source: gene_list
            - source: worst_effect
            - source: gene_effects
        """),
    })
    cli_columns([
        str(root_path / "input" / infile),
        str(root_path / "effect_annotation.yaml"),
        "-o", str(root_path / "result.tsv"),
        "-w", str(root_path / "work"),
        "--grr", str(root_path / "grr.yaml"),
        "-j", "1",
    ])

    df = pd.read_csv(root_path / "result.tsv", sep="\t")
    assert list(df.worst_effect.values) == ["CNV+"]
    assert list(df.gene_effects.values) == ["None:CNV+"]
    assert list(df.gene_list.values) == ["['None']"]


@pytest.mark.parametrize(
    "infile", [
        "bad_cnv.tsv",
    ],
)
def test_bad_cnv_gene_score_annotation(
    infile: str,
    annotate_cnv_fixture: Path,
) -> None:
    root_path = annotate_cnv_fixture
    setup_directories(root_path, {
        "gene_score_annotation.yaml": textwrap.dedent("""
        - effect_annotator:
            gene_models: gene_models/foobar_genes
            genome: genome/foobar_genome
        - gene_score_annotator:
            resource_id: gene_score1
            input_gene_list: gene_list
            attributes:
            - source: gene_score1
              gene_aggregator: max
        """),
    })
    cli_columns([
        str(root_path / "input" / infile),
        str(root_path / "gene_score_annotation.yaml"),
        "-o", str(root_path / "result.tsv"),
        "-w", str(root_path / "work"),
        "--grr", str(root_path / "grr.yaml"),
        "-j", "1",
    ])

    df = pd.read_csv(root_path / "result.tsv", sep="\t")
    assert list(df.worst_effect.values) == ["CNV+"]
    assert all(np.isnan(v) for v in df.gene_score1.values)
