# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceProtocolRepo


def test_effect_annotator(grr_fixture: GenomicResourceProtocolRepo) -> None:
    pipeline = load_pipeline_from_yaml(
        """- effect_annotator:
            gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
            genome: hg38/GRCh38-hg38/genome
        """, grr_fixture,
    )
    assert pipeline
