# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import textwrap
from dae.annotation.annotation_factory import build_annotation_pipeline


def test_effect_annotator_resources(grr_fixture):
    genome = "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome"
    gene_models = "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/" \
        "gene_models/refGene_201309"
    config = textwrap.dedent(f"""
        - effect_annotator:
            genome: {genome}
            gene_models: {gene_models}
        """)

    annotation_pipeline = build_annotation_pipeline(
        pipeline_config_str=config, grr_repository=grr_fixture)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert annotator.resources == {
            genome,
            gene_models
        }
