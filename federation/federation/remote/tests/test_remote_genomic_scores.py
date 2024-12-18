# pylint: disable=W0621,C0114,C0116,W0212,W0613
from gpf_instance.gpf_instance import WGPFInstance
from pytest_mock import MockerFixture

from federation.remote.genomic_scores_registry import (
    RemoteGenomicScoresRegistry,
)
from federation.remote.rest_api_client import RESTClient


def test_remote_genomic_scores(
    mocker: MockerFixture, rest_client: RESTClient,
    remote_t4c8_wgpf_instance: WGPFInstance,
) -> None:
    patch = mocker.patch.object(rest_client, "get_genomic_scores")
    patch.return_value = [{
        "resource_id": "test_resource",
        "score_id": "test_score",
        "source": "attr_source",
        "name": "attr_dest",
        "hist": {
            "config": {
                "type": "number",
                "view_range": {
                    "min": 0,
                    "max": 10,
                },
                "number_of_bins": 10,
                "x_log_scale": False,
                "y_log_scale": False,
                "x_min_log": None,
            },
            "bins": [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
            ],
            "bars": [
                10,
                23,
                50,
                10,
                0,
                6,
                9,
                18,
                31,
                1,
            ],
            "min_value": 1,
            "max_value": 10,
        },
        "description": "ala bala",
        "help": "bala ala",
    }]
    local_db = remote_t4c8_wgpf_instance.genomic_scores

    db = RemoteGenomicScoresRegistry({"remote": rest_client}, local_db)
    assert len(db.remote_scores) == 1
    assert "attr_dest" in db.remote_scores
    score = db.remote_scores["attr_dest"]
    assert score.description == "(TEST_REMOTE) ala bala"
