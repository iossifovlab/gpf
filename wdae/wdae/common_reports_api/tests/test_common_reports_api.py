# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pytest

from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets", "use_common_reports"
)


@pytest.mark.parametrize("url,method,body", [
    ("/api/v3/common_reports/studies/study4", "get", None),
    ("/api/v3/common_reports/studies/study4/full", "get", None),
    (
        "/api/v3/common_reports/family_counters",
        "post",
        {
            "study_id": "study4",
            "group_name": "Phenotype",
            "counter_id": "0"
        }),
    (
        "/api/v3/common_reports/family_counters/download",
        "post",
        {
            "queryData": json.dumps({
                "study_id": "study4",
                "group_name": "Phenotype",
                "counter_id": "0"
            })
        }
    ),
    ("/api/v3/common_reports/families_data/Study1", "get", None),
])
def test_variant_reports_permissions(anonymous_client, url, method, body):
    if method == "get":
        response = anonymous_client.get(url)
    else:
        response = anonymous_client.post(
            url, json.dumps(body), content_type="application/json"
        )

    assert response
    print(response.headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_variant_reports(admin_client):
    url = "/api/v3/common_reports/studies/study4"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data


def test_variant_reports_full(admin_client):
    url = "/api/v3/common_reports/studies/study4/full"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data


def test_family_counters(admin_client):
    data = {
        "study_id": "study4",
        "group_name": "Phenotype",
        "counter_id": "0"
    }
    url = "/api/v3/common_reports/family_counters"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    print(response.data)
    assert data == ["f2", "f4"]


def test_family_counters_download(admin_client):
    data = {
        "queryData": json.dumps({
            "study_id": "study4",
            "group_name": "Phenotype",
            "counter_id": "0"
        })
    }
    url = "/api/v3/common_reports/family_counters/download"
    response = admin_client.post(
        url, json.dumps(data), content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    res = list(response.streaming_content)
    print(b"".join(res).decode())

    assert len(res) == 13
    # assert data == ["f2", "f4"]


def test_families_tags_download(admin_client):
    url = (
        "/api/v3/common_reports/families_data/Study1?"
        "tags=tag_nuclear_family,tag_trio_family"
    )
    response = admin_client.get(
        url, content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    res = list(response.streaming_content)
    print(b"".join(res).decode())
    assert len(res) == 24


def test_families_tags_download_succeeds_on_empty_tags(admin_client):
    url = "/api/v3/common_reports/families_data/Study1?tags="

    response = admin_client.get(
        url, content_type="application/json"
    )

    assert response
    assert response.status_code == status.HTTP_200_OK


def test_variant_reports_no_permissions(user_client):
    url = "/api/v3/common_reports/studies/study4"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN

    data = response.data
    assert data


@pytest.mark.xfail(reason="this test is flipping; should be investigated")
def test_variant_reports_not_found(admin_client):
    url = "/api/v3/common_reports/studies/Study3"
    response = admin_client.get(url)

    assert response
    assert response.data["error"] == "Common report Study3 not found"
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_families_data_download(admin_client):
    url = "/api/v3/common_reports/families_data/Study1"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)
    assert streaming_content

    assert len(streaming_content) == 34


@pytest.mark.xfail(reason="this test is flipping; should be investigated")
def test_families_data_download_no_permissions(user_client):
    url = "/api/v3/common_reports/families_data/study4"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN
