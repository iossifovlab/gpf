import json

from rest_framework import status


PREVIEW_URL = "/api/v3/genotype_browser/preview"
PREVIEW_VARIANTS_URL = "/api/v3/genotype_browser/preview/variants"


def test_query_variants_remote(admin_client, remote_settings):
    data = {"datasetId": "TEST_REMOTE_iossifov_2014"}
    response = admin_client.post(
        PREVIEW_URL, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert "cols" in res
    assert "legend" in res


def test_simple_query_variants_preview(db, admin_client, remote_settings):
    data = {"datasetId": "TEST_REMOTE_iossifov_2014"}

    response = admin_client.post(
        PREVIEW_VARIANTS_URL, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = "".join(map(lambda x: x.decode("utf-8"), res))
    print(res)

    res = json.loads(res)

    print(res)
    print(len(res))
