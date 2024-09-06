# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
import pytest_mock
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


@pytest.mark.skip(reason="interferes with test_pheno_measures_columns")
def test_query_request_simple(
    admin_client: Client,
    mocker: pytest_mock.MockFixture,
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=t4c8_wgpf_instance,
    )

    query = {
        "datasetId": "t4c8_study_1",
        "familyIds": ["f1.1"],
    }
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(query), content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    result = json.loads(
        "".join(ln.decode("utf8") for ln in response.streaming_content))

    assert len(result) == 6
