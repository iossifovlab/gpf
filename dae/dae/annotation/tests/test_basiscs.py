from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_basic():
    grr_repo = GenomicResourceEmbededRepo("r", {
        "one": {
            GR_CONF_FILE_NAME: '''
                type: PositionScore
                table:
                    filename: data.mem
                scores:
                  - id: s1
                    type: float
                    name: s1''',
            "data.mem": '''
                chrom  pos_begin  s1
                1      10         0.02
                1      11         0.03
                1      15         0.46
                2      8          0.01
                '''
        }
    })
    annotation_cofiguration = """
    - position_score:
        resource_id: one
    """
    ann_pipe = AnnotationPipeline.build(
        pipeline_config_str=annotation_cofiguration,
        grr_repository=grr_repo,
        context=None)
    assert grr_repo
    assert ann_pipe
