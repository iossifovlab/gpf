from dae.annotation.annotation_factory import build_annotation_pipeline


def test_empty():
    pipeline = build_annotation_pipeline([])
    assert pipeline


def test_effect_annotator(grr_fixture):
    pipeline = build_annotation_pipeline(
        grr_repository=grr_fixture,
        pipeline_config_str="""
        - effect_annotator:
            gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
            genome: hg38/GRCh38-hg38/genome
        """)
    assert pipeline
