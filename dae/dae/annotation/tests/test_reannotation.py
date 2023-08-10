# pylint: disable=missing-function-docstring,redefined-outer-name
# type: ignore
import textwrap
import pytest
from dae.genomic_resources import build_genomic_resource_repository
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import ReannotationPipeline

from dae.testing.foobar_import import foobar_genome, foobar_genes
from dae.testing import setup_directories, convert_to_tab_separated, \
    setup_genome, setup_denovo

from dae.annotation.annotate_columns import cli as cli_columns


@pytest.fixture(scope="module")
def root_path(tmp_path_factory):
    return tmp_path_factory.mktemp("reannotation_grr")


@pytest.fixture(scope="module")
def reannotation_grr(root_path):
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
        """
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
                    """)
                },
                "foobar_genome_2": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: genome
                        filename: chrAll.fa
                    """)
                },
                "foobar_genes": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: gene_models
                        filename: genes.txt
                        format: refflat
                    """)
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
                    """)
                },
                "gene_score1": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: gene_score
                        filename: score.csv
                        scores:
                        - id: gene_score1
                          desc: Test gene score
                          number_hist:
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
                          number_hist:
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
                }
            },
            "reannotation_old.yaml": textwrap.dedent("""
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
            "reannotation_new.yaml": textwrap.dedent("""
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
        }
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml"
    ))


def test_annotators_used_context(reannotation_grr) -> None:
    pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=reannotation_grr
    )
    assert pipeline.annotators[0].used_context_attributes == \
        tuple()
    assert pipeline.annotators[1].used_context_attributes == \
        ("hgX_annotatable",)
    assert pipeline.annotators[2].used_context_attributes == \
        ("my_genes",)


def test_dependency_graph_construction(reannotation_grr) -> None:
    pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=reannotation_grr
    )
    dependency_graph = ReannotationPipeline.build_dependency_graph(pipeline)

    liftover = pipeline.annotators[0].get_info()
    effect = pipeline.annotators[1].get_info()
    gene_score = pipeline.annotators[2].get_info()

    assert len(dependency_graph) == 3

    assert dependency_graph[liftover] == []

    assert len(dependency_graph[effect]) == 1
    assert dependency_graph[effect][0][0] == liftover
    assert dependency_graph[effect][0][1].name == "hgX_annotatable"

    assert len(dependency_graph[gene_score]) == 1
    assert dependency_graph[gene_score][0][0] == effect
    assert dependency_graph[gene_score][0][1].name == "my_genes"


def test_basic_annotator_changes_detection(reannotation_grr) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    - gene_score_annotator:
        resource_id: gene_score2
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    - position_score: one
    """
    old_pipeline = build_annotation_pipeline(
        pipeline_config_str=old_pipeline_config,
        grr_repository=reannotation_grr
    )
    new_pipeline = build_annotation_pipeline(
        pipeline_config_str=new_pipeline_config,
        grr_repository=reannotation_grr
    )
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.attributes_deleted) == 1
    assert len(reannotation.annotators_rerun) == 0
    assert len(reannotation.attributes_reused) == 0


def test_upstream_change_detection(reannotation_grr) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
          internal: true
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
          internal: true
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score2
        input_gene_list: my_genes
    """
    old_pipeline = build_annotation_pipeline(
        pipeline_config_str=old_pipeline_config,
        grr_repository=reannotation_grr
    )
    new_pipeline = build_annotation_pipeline(
        pipeline_config_str=new_pipeline_config,
        grr_repository=reannotation_grr
    )
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.attributes_deleted) == 1
    assert len(reannotation.annotators_rerun) == 2
    assert len(reannotation.attributes_reused) == 0


def test_downstream_change_detection(reannotation_grr) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome_2
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    old_pipeline = build_annotation_pipeline(
        pipeline_config_str=old_pipeline_config,
        grr_repository=reannotation_grr
    )
    new_pipeline = build_annotation_pipeline(
        pipeline_config_str=new_pipeline_config,
        grr_repository=reannotation_grr
    )
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.attributes_deleted) == 1
    assert len(reannotation.annotators_rerun) == 2
    assert len(reannotation.attributes_reused) == 0


def test_reused_attributes_detection_simple(reannotation_grr) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    - gene_score_annotator:
        resource_id: gene_score2
        input_gene_list: my_genes
    """
    old_pipeline = build_annotation_pipeline(
        pipeline_config_str=old_pipeline_config,
        grr_repository=reannotation_grr
    )
    new_pipeline = build_annotation_pipeline(
        pipeline_config_str=new_pipeline_config,
        grr_repository=reannotation_grr
    )
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.annotators_rerun) == 0
    assert len(reannotation.attributes_deleted) == 0
    assert len(reannotation.attributes_reused) == 1


def test_reused_attributes_detection_indirect(reannotation_grr) -> None:
    old_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    """
    new_pipeline_config = """
    - liftover_annotator:
        chain: foobar_chain
        target_genome: foobar_genome
        attributes:
        - destination: hgX_annotatable
          source: liftover_annotatable
    - effect_annotator:
        genome: foobar_genome
        gene_models: foobar_genes
        input_annotatable: hgX_annotatable
        attributes:
        - destination: my_genes
          source: gene_list
          internal: true
    - gene_score_annotator:
        resource_id: gene_score1
        input_gene_list: my_genes
    - gene_score_annotator:
        resource_id: gene_score2
        input_gene_list: my_genes
    """
    old_pipeline = build_annotation_pipeline(
        pipeline_config_str=old_pipeline_config,
        grr_repository=reannotation_grr
    )
    new_pipeline = build_annotation_pipeline(
        pipeline_config_str=new_pipeline_config,
        grr_repository=reannotation_grr
    )
    reannotation = ReannotationPipeline(new_pipeline, old_pipeline)

    assert len(reannotation.annotators_new) == 1
    assert len(reannotation.annotators_rerun) == 1
    assert len(reannotation.attributes_deleted) == 0
    assert len(reannotation.attributes_reused) == 1


def test_annotate_columns_reannotation(
    root_path, reannotation_grr  # pylint: disable=unused-argument
):
    in_content = (
        "chrom\tpos\tscore\tworst_effect\tgene_effects\teffect_details\tgene_list\tgene_score1\tgene_score2\n"  # noqa
        "chr1\t23\t0.1\tbla\tbla\tbla\tbla\tbla\tbla\n"
    )
    out_expected_header = [
        "chrom", "pos", "score", "worst_effect", "gene_list", "gene_score1"
    ]
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file_old = root_path / "reannotation_old.yaml"
    annotation_file_new = root_path / "reannotation_new.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file_new, "-o", out_file, "--grr", grr_file,
            "--reannotate", annotation_file_old
        ]
    ])
    with open(out_file, "rt", encoding="utf8") as _:
        out_file_header = "".join(_.readline()).strip().split("\t")
    assert out_file_header == out_expected_header
