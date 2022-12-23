# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.genomic_resources.testing import build_inmemory_test_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.annotation.annotation_factory import build_annotation_pipeline


def test_basic(tmp_path):
    grr_repo = build_inmemory_test_repository({
        "one": {
            GR_CONF_FILE_NAME: """
                type: position_score
                table:
                    filename: data.mem
                scores:
                - id: s1
                  type: float
                  name: s1""",
            "data.mem": """
                chrom  pos_begin  s1
                1      10         0.02
                1      11         0.03
                1      15         0.46
                2      8          0.01
                """
        }
    })
    annotation_cofiguration = """
    - position_score:
        resource_id: one
    """
    ann_pipe = build_annotation_pipeline(
        pipeline_config_str=annotation_cofiguration,
        grr_repository=grr_repo)
    assert grr_repo
    assert ann_pipe
