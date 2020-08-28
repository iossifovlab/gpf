import copy
import json
import pytest

from django.contrib.auth.models import Group

from rest_framework import status

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


EXAMPLE_REQUEST_F1 = {
    "datasetId": "quads_f1",
}


PREVIEW_URL = "/api/v3/genotype_browser/preview"
PREVIEW_VARIANTS_URL = "/api/v3/genotype_browser/preview/variants"
DOWNLOAD_URL = "/api/v3/genotype_browser/download"


@pytest.mark.xfail
def test_simple_preview(db, admin_client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)

    response = admin_client.post(
        PREVIEW_URL, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert "cols" in res
    assert "legend" in res

    assert len(res["legend"]) == 8
    assert len(res["cols"]) == 19


def test_simple_query_variants_preview(db, admin_client):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)

    response = admin_client.post(
        PREVIEW_VARIANTS_URL, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 3


@pytest.mark.parametrize("url", [PREVIEW_URL, PREVIEW_VARIANTS_URL])
def test_missing_dataset(db, user_client, url):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    del data["datasetId"]

    response = user_client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_400_BAD_REQUEST, response.status_code


@pytest.mark.parametrize("url", [PREVIEW_URL, PREVIEW_VARIANTS_URL])
def test_bad_dataset(db, user_client, url):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    data["datasetId"] = "ala bala portokala"

    response = user_client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_400_BAD_REQUEST, response.status_code


def test_simple_query_download(db, admin_client):
    data = {"queryData": json.dumps(EXAMPLE_REQUEST_F1)}

    response = admin_client.post(
        DOWNLOAD_URL, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)
    assert res
    assert res[0]
    header = res[0].decode("utf-8")[:-1].split("\t")

    assert len(res) == 4

    assert set(header) == {
        "family id",
        "study",
        "phenotype",
        "location",
        "variant",
        "family genotype",
        "from parent",
        "in child",
        "worst effect type",
        "genes",
        "count",
        "all effects",
        "effect details",
        "LGD rank",
        "RVIS rank",
        "pLI rank",
        "SSC",
        "EVS",
        "E65",
        "categorical.Categorical",
        "continuous.Continuous",
        "ordinal.Ordinal",
        "raw.Raw",
    }


def test_mixed_dataset_rights_query(db, user, user_client):
    data = {
        "datasetId": "composite_dataset_ds",
    }

    group = Group.objects.get(name="inheritance_trio")
    user.groups.add(group)

    response = user_client.post(
        PREVIEW_VARIANTS_URL, json.dumps(data), content_type="application/json"
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 14


def test_mixed_dataset_rights_download(db, user, user_client):
    data = {
        "queryData": json.dumps({"datasetId": "composite_dataset_ds"})
    }

    group = Group.objects.get(name="inheritance_trio")
    user.groups.add(group)

    response = user_client.post(
        DOWNLOAD_URL, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)
    assert len(res) == 15
