# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.genomic_resources.repository import GenomicResourceProtocolRepo


def test_empty() -> None:
    pipeline = build_annotation_pipeline([])
    assert pipeline is not None


def test_effect_annotator(grr_fixture: GenomicResourceProtocolRepo) -> None:
    pipeline = build_annotation_pipeline(
        grr_repository=grr_fixture,
        pipeline_config_str="""
        - effect_annotator:
            gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
            genome: hg38/GRCh38-hg38/genome
        """)
    assert pipeline
