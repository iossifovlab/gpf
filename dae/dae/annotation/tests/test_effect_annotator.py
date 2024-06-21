# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import textwrap

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceRepo


def test_effect_annotator_resources(
        grr_fixture: GenomicResourceRepo) -> None:
    genome = "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome"
    gene_models = "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/" \
        "gene_models/refGene_201309"
    config = textwrap.dedent(f"""
        - effect_annotator:
            genome: {genome}
            gene_models: {gene_models}
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr_fixture)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {
            genome,
            gene_models,
        }


def test_effect_annotator_documentation(
        grr_fixture: GenomicResourceRepo) -> None:

    pipeline = load_pipeline_from_yaml(textwrap.dedent(
        """
        - effect_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
            gene_models: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/gene_models/refGene_201309
        """),  # noqa
        grr_fixture)

    att = pipeline.get_attribute_info("worst_effect")
    assert att is not None
    assert "Worst" in att.documentation
