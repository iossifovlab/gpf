# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_inmemory_test_repository


def test_basic() -> None:
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
                """,
        },
    })
    config = """
    - position_score:
        resource_id: one
    """
    ann_pipe = load_pipeline_from_yaml(config, grr_repo)
    assert grr_repo
    assert ann_pipe
