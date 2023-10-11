# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pytest_mock import MockerFixture
from remote.genomic_scores_db import RemoteGenomicScoresDb
from remote.rest_api_client import RESTClient
from gpf_instance.gpf_instance import WGPFInstance


def test_remote_genomic_scores(
    mocker: MockerFixture, rest_client: RESTClient,
    wdae_gpf_instance: WGPFInstance
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
                    "max": 10
                },
                "number_of_bins": 10,
                "x_log_scale": False,
                "y_log_scale": False,
                "x_min_log": None
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
                10
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
                1
            ],
            "min_value": 1,
            "max_value": 10
        },
        "description": "ala bala",
        "help": "bala ala"
    }]
    local_db = wdae_gpf_instance.genomic_scores_db
    db = RemoteGenomicScoresDb([rest_client], local_db)
    assert len(db.remote_scores) == 1
    assert "test_score" in db.remote_scores
    score = db.remote_scores["test_score"]
    assert score.description == "(TEST_REMOTE) ala bala"
