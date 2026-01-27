# pylint: disable=missing-function-docstring,redefined-outer-name
# flake8: noqa
import pathlib
import textwrap

import pysam
import pytest
from dae.annotation.annotate_columns import cli as cli_columns
from dae.annotation.annotate_vcf import cli as cli_vcf
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    convert_to_tab_separated,
    setup_denovo,
    setup_directories,
    setup_genome,
    setup_vcf,
)
import pytest_mock
import dae.annotation.annotate_columns
import dae.annotation.annotate_vcf
from dae.testing.foobar_import import foobar_genes, foobar_genome

pytestmark = pytest.mark.usefixtures("clean_genomic_context")


@pytest.fixture
def reannotation_grr(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path
    foobar_genome(root_path / "grr")
    foobar_genes(root_path / "grr")
    setup_genome(
        root_path / "foobar_genome_2" / "chrAll.fa",
        """
            >foo
            NNACCCAAAC
            GGGCCTTCCN
            NNNA
            >bar
            NNGGGCCTTC
            CACGACCCAA
            NN
        """,
    )

    setup_directories(
        root_path, {
            "grr.yaml": textwrap.dedent(f"""
                id: reannotation_repo
                type: dir
                directory: "{root_path}/grr"
            """),
            "grr": {
                "foobar_genome": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: genome
                        filename: chrAll.fa
                    """),
                },
                "foobar_genome_2": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: genome
                        filename: chrAll.fa
                    """),
                },
                "foobar_genes": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: gene_models
                        filename: genes.txt
                        format: refflat
                    """),
                },
                "foobar_chain": {
                    "genomic_resource.yaml": """
                        type: liftover_chain
                        filename: test.chain
                    """,
                    "test.chain": "blabla",
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
                "gene_score2": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: gene_score
                        filename: score.csv
                        scores:
                        - id: gene_score2
                          desc: Test gene score
                          histogram:
                            type: number
                            number_of_bins: 100
                            view_range:
                              min: 0.0
                              max: 56.0
                    """),
                    "score.csv": textwrap.dedent("""
                        gene,gene_score2
                        g1,20.2
                        g2,40.4
                    """),
                },
            },
            "reannotation_old.yaml": textwrap.dedent("""
                preamble:
                  input_reference_genome: foobar_genome
                annotators:
                  - position_score: one
                  - effect_annotator:
                      genome: foobar_genome
                      gene_models: foobar_genes
                  - gene_score_annotator:
                      resource_id: gene_score1
                      input_gene_list: gene_list
                  - gene_score_annotator:
                      resource_id: gene_score2
                      input_gene_list: gene_list
            """),
            "reannotation_old_internal.yaml": textwrap.dedent("""
                preamble:
                  input_reference_genome: foobar_genome
                annotators:
                  - position_score: one
                  - effect_annotator:
                      genome: foobar_genome
                      gene_models: foobar_genes
                  - gene_score_annotator:
                      resource_id: gene_score1
                      input_gene_list: gene_list
                  - gene_score_annotator:
                      resource_id: gene_score2
                      input_gene_list: gene_list
                      attributes:
                      - source: gene_score2
                        name: gene_score2
                        internal: true
            """),
            "reannotation_new.yaml": textwrap.dedent("""
                preamble:
                  input_reference_genome: foobar_genome
                annotators:
                  - position_score: one
                  - effect_annotator:
                      genome: foobar_genome
                      gene_models: foobar_genes
                      attributes:
                      - worst_effect
                      - gene_list
                  - gene_score_annotator:
                      resource_id: gene_score1
                      input_gene_list: gene_list
            """),
        },
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml",
    ))


def test_annotate_columns_reannotation(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
    mocker: pytest_mock.MockerFixture,
) -> None:
    assert reannotation_grr is not None
    in_content = (
        "chrom\tpos\tscore\tworst_effect\teffect_details\tgene_effects\tgene_score1\tgene_score2\n"  
        "chr1\t23\t0.1\tbla\tbla\tbla\tbla\tbla\n"
    )
    out_expected_header = [
        "chrom", "pos", "score", "worst_effect", "gene_score1",
    ]
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    annotation_file_old = tmp_path / "reannotation_old.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    spy = mocker.spy(dae.annotation.annotate_columns,
                     "ReannotationPipeline")

    cli_columns([
        str(a) for a in [
            in_file, annotation_file_new,
            "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--reannotate", annotation_file_old,
            "-j", 1,
        ]
    ])

    with open(out_file, "rt", encoding="utf8") as _:
        out_file_header = "".join(_.readline()).strip().split("\t")
    assert spy.call_count == 1
    assert out_file_header == out_expected_header


def test_annotate_columns_reannotation_internal(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
    mocker: pytest_mock.MockerFixture,
) -> None:
    assert reannotation_grr is not None
    in_content = (
        "chrom\tpos\tscore\tworst_effect\teffect_details\tgene_effects\tgene_score1\n"
        "chr1\t23\t0.1\tbla\tbla\tbla\tbla\n"
    )
    out_expected_header = [
        "chrom", "pos", "score", "worst_effect", "gene_score1",
    ]
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    annotation_file_old = tmp_path / "reannotation_old_internal.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    spy = mocker.spy(dae.annotation.annotate_columns,
                     "ReannotationPipeline")

    cli_columns([
        str(a) for a in [
            in_file, annotation_file_new,
            "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--reannotate", annotation_file_old,
            "-j", 1,
        ]
    ])
    with open(out_file, "rt", encoding="utf8") as _:
        out_file_header = "".join(_.readline()).strip().split("\t")
    assert spy.call_count == 1
    assert out_file_header == out_expected_header


def test_annotate_columns_reannotation_batched(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
    mocker: pytest_mock.MockerFixture,
) -> None:
    assert reannotation_grr is not None
    in_content = (
        "chrom\tpos\tscore\tworst_effect\teffect_details\tgene_effects\tgene_score1\tgene_score2\n"
        "chr1\t23\t0.1\tbla\tbla\tbla\tbla\tbla\n"
        "chr1\t24\t0.1\tbla\tbla\tbla\tbla\tbla\n"
        "chr1\t25\t0.1\tbla\tbla\tbla\tbla\tbla\n"
        "chr1\t26\t0.1\tbla\tbla\tbla\tbla\tbla\n"
    )
    out_expected_header = [
        "chrom", "pos", "score", "worst_effect", "gene_score1",
    ]
    in_file = tmp_path / "in.txt"
    out_path = tmp_path / "out.txt"
    annotation_file_old = tmp_path / "reannotation_old.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    spy = mocker.spy(dae.annotation.annotate_columns,
                     "ReannotationPipeline")

    cli_columns([
        str(a) for a in [
            in_file, annotation_file_new,
            "-o", out_path,
            "-w", work_dir,
            "--grr", grr_file,
            "--reannotate", annotation_file_old,
            "-j", 1,
            "--batch-size", 2,
        ]
    ])

    with open(out_path, "rt", encoding="utf8") as out_file:
        out_file_header = "".join(out_file.readline()).strip().split("\t")
        lines = out_file.readlines()
    assert spy.call_count == 1
    assert out_file_header == out_expected_header
    assert len(lines) == 4


def test_annotate_vcf_reannotation(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
    mocker: pytest_mock.MockerFixture,
) -> None:
    assert reannotation_grr is not None
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##INFO=<ID=score,Number=A,Type=Float,Description="">
        ##INFO=<ID=worst_effect,Number=A,Type=String,Description="">
        ##INFO=<ID=effect_details,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_effects,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_list,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_score1,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_score2,Number=A,Type=String,Description="">
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER \
INFO                                                  \
                                               FORMAT m1  d1  c1
        foo    12  .  C   T   .    .      \
score=0.1;worst_effect=splice-site;effect_details=bla;gene_effects=bla;\
gene_list=g1;gene_score1=10.1;gene_score2=20.2 GT     0/1 0/0 0/0
    """)

    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    annotation_file_old = tmp_path / "reannotation_old.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_vcf(in_file, in_content)

    spy = mocker.spy(dae.annotation.annotate_vcf,
                     "ReannotationPipeline")

    cli_vcf([
        str(a) for a in [
            in_file,
            annotation_file_new,
            "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--reannotate", annotation_file_old,
            "-j", 1,
        ]
    ])
    out_vcf = pysam.VariantFile(str(out_file))

    info_keys = set(out_vcf.header.info.keys())

    assert spy.call_count == 1
    assert info_keys == {  # pylint: disable=no-member
        "score", "worst_effect", "gene_list", "gene_score1",
    }


def test_annotate_vcf_reannotation_batch(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
    mocker: pytest_mock.MockerFixture,
) -> None:
    assert reannotation_grr is not None

    info = ("worst_effect=splice-site;effect_details=bla;gene_effects=bla"
            ";gene_list=g1;gene_score1=10.1;gene_score2=20.2")

    in_content = textwrap.dedent(f"""
        ##fileformat=VCFv4.2
        ##INFO=<ID=score,Number=A,Type=Float,Description="">
        ##INFO=<ID=worst_effect,Number=A,Type=String,Description="">
        ##INFO=<ID=effect_details,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_effects,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_list,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_score1,Number=A,Type=String,Description="">
        ##INFO=<ID=gene_score2,Number=A,Type=String,Description="">
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO             FORMAT m1  d1  c1
        foo    12  .  C   T   .    .      score=0.1;{info} GT     0/1 0/0 0/0
        foo    24  .  C   T   .    .      score=0.1;{info} GT     0/1 0/0 0/0
        foo    48  .  C   T   .    .      score=0.1;{info} GT     0/1 0/0 0/0
        foo    96  .  C   T   .    .      score=0.1;{info} GT     0/1 0/0 0/0
    """)

    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    annotation_file_old = tmp_path / "reannotation_old.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_vcf(in_file, in_content)

    spy = mocker.spy(dae.annotation.annotate_vcf,
                     "ReannotationPipeline")

    cli_vcf([
        str(a) for a in [
            in_file,
            annotation_file_new,
            "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--reannotate", annotation_file_old,
            "-j", 1,
            "--batch-size", 2,
        ]
    ])
    out_vcf = pysam.VariantFile(str(out_file))

    info_keys = set(out_vcf.header.info.keys())

    assert spy.call_count == 1
    assert info_keys == {  # pylint: disable=no-member
        "score", "worst_effect", "gene_list", "gene_score1",
    }
