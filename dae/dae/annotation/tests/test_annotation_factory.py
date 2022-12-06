# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.annotation.annotation_factory import build_annotation_pipeline, \
    build_np_score_annotator


@pytest.fixture(scope="session")
def grr_np_score1() -> GenomicResourceRepo:
    repo = build_genomic_resource_repository({
        "id": "test_annotation",
        "type": "embedded",
        "content": {
            "np_score1": {
                "genomic_resource.yaml":
                """\
                type: np_score
                table:
                    filename: data.mem
                    scores:
                        - id: test_raw
                          type: float
                          desc: "test values"
                          name: raw
                """,
                "data.mem": """
                    chrom  pos_begin  reference alternative raw
                    1      14968      A         C           0.00001
                    1      14968      A         G           0.00002
                    1      14968      A         T           0.00004
                    1      14969      C         A           0.0001
                    1      14969      C         G           0.0002
                    1      14969      C         T           0.0004
                """
            }
        }
    })
    return repo


@pytest.fixture(scope="session")
def annotation_pipeline1(grr_np_score1):
    pipeline = build_annotation_pipeline(
        pipeline_config=[],
        grr_repository=grr_np_score1)

    return pipeline


def test_annotation_factory_np_score(annotation_pipeline1):
    config = {
        "annotator_type": "np_score",
        "resource_id": "np_score1",
        "attributes": [
            {
                "source": "raw",
                "destination": "np_score1",
            },
        ],
    }

    annotator = build_np_score_annotator(annotation_pipeline1, config)
    assert annotator is not None
