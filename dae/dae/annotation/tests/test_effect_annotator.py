import textwrap
from dae.annotation.annotation_factory import build_annotation_pipeline


def test_effect_annotator_resource_files(grr_fixture):

    GATK = "GATK_ResourceBundle_5777_b37_phiX174_short"
    genome = f"hg19/{GATK}/genome"
    gene_models = f"hg19/{GATK}/gene_models/refGene_201309"
    config = textwrap.dedent(f"""
        - effect_annotator:
            genome: {genome}
            gene_models: {gene_models}
        """)

    annotation_pipeline = build_annotation_pipeline(
        pipeline_config_str=config, grr_repository=grr_fixture)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert annotator.resource_files == {
            genome: {"chrAll.fa", "chrAll.fa.fai", },
            gene_models: {"refGene201309.txt", }
        }
