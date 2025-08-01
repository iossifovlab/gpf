# pylint: disable=missing-function-docstring,redefined-outer-name
import pathlib
import textwrap

import pysam
import pytest
from dae.annotation.annotate_columns import cli as cli_columns
from dae.annotation.annotate_vcf import cli as cli_vcf
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.annotation_pipeline import (
    ReannotationPipeline,
    _build_dependency_graph,
    get_deleted_attributes,
)
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.testing import (
    convert_to_tab_separated,
    setup_denovo,
    setup_directories,
    setup_genome,
    setup_vcf,
)
from dae.testing.foobar_import import foobar_genes, foobar_genome


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
                        gene,gene_score1
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


@pytest.fixture
def simple_pipeline_config() -> str:
    return """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - name: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """


def test_annotators_used_context_attributes(
    simple_pipeline_config: str, reannotation_grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        simple_pipeline_config, reannotation_grr)
    # default behaviour
    assert pipeline.annotators[0].used_context_attributes == ()

    # input annotatable, any annotator
    assert pipeline.annotators[1].used_context_attributes == \
        ("hgX_annotatable",)

    # gene score annotator's input_gene_list
    assert pipeline.annotators[2].used_context_attributes == \
        ("my_genes",)


def test_dependency_graph_correctness(
    simple_pipeline_config: str, reannotation_grr: GenomicResourceRepo,
) -> None:
    pipeline = load_pipeline_from_yaml(
        simple_pipeline_config, reannotation_grr)
    dependency_graph = _build_dependency_graph(pipeline)

    liftover_annotator = pipeline.annotators[0].get_info()
    effect_annotator = pipeline.annotators[1].get_info()
    gene_score_annotator = pipeline.annotators[2].get_info()

    # All annotators are in the dependency graph
    assert len(dependency_graph) == 3

    # Liftover annotator does not depend on anything
    assert dependency_graph[liftover_annotator] == []

    # Effect annotator depends on liftover annotator
    assert len(dependency_graph[effect_annotator]) == 1
    assert dependency_graph[effect_annotator][0][0] == liftover_annotator
    assert dependency_graph[effect_annotator][0][1].name == "hgX_annotatable"

    # Gene score annotator depends on effect annotator
    assert len(dependency_graph[gene_score_annotator]) == 1
    assert dependency_graph[gene_score_annotator][0][0] == effect_annotator
    assert dependency_graph[gene_score_annotator][0][1].name == "my_genes"


def test_new_annotators_detection(
        reannotation_grr: GenomicResourceRepo) -> None:
    old_pipeline_config = """
    - position_score: one
    """
    new_pipeline_config = """
    - position_score: one
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    """
    old_pipeline = load_pipeline_from_yaml(
        old_pipeline_config, reannotation_grr)
    new_pipeline = load_pipeline_from_yaml(
        new_pipeline_config, reannotation_grr)
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.annotators_rerun) == 0


def test_deleted_attributes(reannotation_grr: GenomicResourceRepo) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: liftover_annotatable
    - position_score: one
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
    - position_score: one
    """
    old_pipeline = load_pipeline_from_yaml(
        old_pipeline_config, reannotation_grr)
    new_pipeline = load_pipeline_from_yaml(
        new_pipeline_config, reannotation_grr)

    attributes_to_delete = get_deleted_attributes(
        new_pipeline.get_info(), old_pipeline.get_info(),
    )

    assert attributes_to_delete == [
        "worst_effect", "effect_details", "gene_effects",
    ]


def test_reused_attributes(
        reannotation_grr: GenomicResourceRepo) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
    """
    old_pipeline = load_pipeline_from_yaml(
        old_pipeline_config, reannotation_grr)
    new_pipeline = load_pipeline_from_yaml(
        new_pipeline_config, reannotation_grr)
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.annotators_rerun) == 0


def test_reused_attributes_indirect(
        reannotation_grr: GenomicResourceRepo) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - name: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - name: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    - gene_score_annotator:
        resource_id: gene_score2
        input_gene_list: my_genes
    """
    old_pipeline = load_pipeline_from_yaml(
        old_pipeline_config, reannotation_grr)
    new_pipeline = load_pipeline_from_yaml(
        new_pipeline_config, reannotation_grr)
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.annotators_rerun) == 1


def test_annotators_rerun_detection_upstream(
        reannotation_grr: GenomicResourceRepo) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
          internal: true
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - name: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
          internal: true
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - name: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score2
        input_gene_list: my_genes
    """
    old_pipeline = load_pipeline_from_yaml(
        old_pipeline_config, reannotation_grr)
    new_pipeline = load_pipeline_from_yaml(
        new_pipeline_config, reannotation_grr)
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.annotators_rerun) == 2


def test_annotators_rerun_detection_downstream(
        reannotation_grr: GenomicResourceRepo) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - name: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        source_genome: foobar_genome_2
        target_genome: foobar_genome_2
        attributes:
        - name: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - name: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    old_pipeline = load_pipeline_from_yaml(
        old_pipeline_config, reannotation_grr)
    new_pipeline = load_pipeline_from_yaml(
        new_pipeline_config, reannotation_grr)
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.annotators_rerun) == 2


def test_annotate_columns_reannotation(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
) -> None:
    assert reannotation_grr is not None
    in_content = (
        "chrom\tpos\tscore\tworst_effect\teffect_details\tgene_effects\tgene_score1\tgene_score2\n"
        "chr1\t23\t0.1\tbla\tbla\tbla\tbla\tbla\n"
    )
    out_expected_header = [
        "chrom", "pos", "score", "worst_effect", "gene_list", "gene_score1",
    ]
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    annotation_file_old = tmp_path / "reannotation_old.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

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
    assert out_file_header == out_expected_header


def test_annotate_columns_reannotation_internal(
    tmp_path: pathlib.Path, reannotation_grr: GenomicResourceRepo,
) -> None:
    assert reannotation_grr is not None
    in_content = (
        "chrom\tpos\tscore\tworst_effect\teffect_details\tgene_effects\tgene_score1\n"
        "chr1\t23\t0.1\tbla\tbla\tbla\tbla\n"
    )
    out_expected_header = [
        "chrom", "pos", "score", "worst_effect", "gene_list", "gene_score1",
    ]
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    annotation_file_old = tmp_path / "reannotation_old_internal.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

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
    assert out_file_header == out_expected_header


def test_annotate_columns_reannotation_batched(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
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
        "chrom", "pos", "score", "worst_effect", "gene_list", "gene_score1",
    ]
    in_file = tmp_path / "in.txt"
    out_path = tmp_path / "out.txt"
    annotation_file_old = tmp_path / "reannotation_old.yaml"
    annotation_file_new = tmp_path / "reannotation_new.yaml"
    grr_file = tmp_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

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
    assert out_file_header == out_expected_header
    assert len(lines) == 4


def test_annotate_vcf_reannotation(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
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

    assert info_keys == {  # pylint: disable=no-member
        "score", "worst_effect", "gene_list", "gene_score1",
    }


def test_annotate_vcf_reannotation_batch(
    tmp_path: pathlib.Path,
    reannotation_grr: GenomicResourceRepo,
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

    assert info_keys == {  # pylint: disable=no-member
        "score", "worst_effect", "gene_list", "gene_score1",
    }
