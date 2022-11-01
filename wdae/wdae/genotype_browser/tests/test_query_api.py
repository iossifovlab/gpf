# pylint: disable=W0621,C0114,C0116,W0212,W0613

import copy
import json
import pytest

from datasets_api.permissions import add_group_perm_to_user, \
    add_group_perm_to_dataset
from rest_framework import status  # type: ignore


pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


EXAMPLE_REQUEST_F1 = {
    "datasetId": "quads_f1",
}


QUERY_VARIANTS_URL = "/api/v3/genotype_browser/query"
JSON_CONTENT_TYPE = "application/json"


def test_simple_query(db, admin_client, preview_sources):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    data["sources"] = list(preview_sources)

    response = admin_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )

    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 3


def test_simple_query_download_anonymous(
        db, anonymous_client, download_sources):
    data = {
        **EXAMPLE_REQUEST_F1,
        "download": True,
        "sources": download_sources
    }
    response = anonymous_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_simple_query_download(db, admin_client, download_sources):
    data = {
        **EXAMPLE_REQUEST_F1,
        "download": True,
        "sources": download_sources
    }

    response = admin_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)
    assert res
    assert res[0]
    header = res[0].decode("utf-8")[:-1].split("\t")

    assert len(res) == 4

    assert set(header) == {
        "family id",
        "studyName",
        "phenotype",
        "location",
        "variant",
        "bestSt",
        "fromParentS",
        "inChS",
        "worstEffect",
        "genes",
        "counts",
        "geneEffect",
        "effectDetails",
        "LGD_rank",
        "RVIS_rank",
        "pLI_rank",
        "SSC-freq",
        "EVS-freq",
        "E65-freq",
        "instrument1.categorical",
        "instrument1.continuous",
        "instrument1.ordinal",
        "instrument1.raw",
    }


def test_simple_query_summary_variants(
    db, admin_client, summary_preview_sources
):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    data["sources"] = list(summary_preview_sources)

    response = admin_client.post(
        QUERY_VARIANTS_URL,
        json.dumps(data),
        content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 3


def test_simple_query_summary_variants_download(
    db, admin_client, summary_download_sources
):
    data = {
        **EXAMPLE_REQUEST_F1,
        "download": True,
        "sources": summary_download_sources
    }

    response = admin_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)
    assert res
    assert res[0]
    header = res[0].decode("utf-8")[:-1].split("\t")

    assert len(res) == 4

    assert set(header) == {
        "location",
        "variant",
        "worstEffect",
        "genes",
        "geneEffect",
        "effectDetails",
        "LGD_rank",
        "RVIS_rank",
        "pLI_rank",
        "SSC-freq",
        "EVS-freq",
        "E65-freq",
        "instrument1.categorical",
        "instrument1.continuous",
        "instrument1.ordinal",
        "instrument1.raw",
    }


@pytest.mark.parametrize("url", [QUERY_VARIANTS_URL])
def test_missing_dataset(db, user_client, url, preview_sources):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    data["sources"] = list(preview_sources)
    del data["datasetId"]

    response = user_client.post(
        url, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_400_BAD_REQUEST, response.status_code


@pytest.mark.parametrize("url", [QUERY_VARIANTS_URL])
def test_bad_dataset(db, user_client, url, preview_sources):
    data = copy.deepcopy(EXAMPLE_REQUEST_F1)
    data["sources"] = list(preview_sources)
    data["datasetId"] = "ala bala portokala"

    response = user_client.post(
        url, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_400_BAD_REQUEST, response.status_code


# START: Adaptive datasets rights
def test_normal_dataset_rights_query(db, user, user_client, preview_sources):
    data = {
        "datasetId": "composite_dataset_ds",
        "sources": list(preview_sources),
    }

    add_group_perm_to_user("composite_dataset_ds", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 17


def test_mixed_dataset_rights_query(db, user, user_client, preview_sources):
    data = {
        "datasetId": "composite_dataset_ds",
        "sources": list(preview_sources),
    }

    add_group_perm_to_user("inheritance_trio", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 14


def test_mixed_layered_dataset_rights_query(
    db, user, user_client, preview_sources
):
    data = {
        "datasetId": "composite_dataset_ds",
        "sources": list(preview_sources),
    }

    add_group_perm_to_user("inheritance_trio", user)
    add_group_perm_to_user("composite_dataset_ds", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 17


def test_mixed_layered_diff_group_dataset_rights_query(
    db, user, user_client, preview_sources
):
    data = {
        "datasetId": "composite_dataset_ds",
        "sources": list(preview_sources),
    }

    add_group_perm_to_dataset("new_custom_group", "composite_dataset_ds")
    add_group_perm_to_dataset("new_custom_group", "inheritance_trio")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 17


def test_mixed_dataset_rights_download(
    db, user, user_client, download_sources
):
    data = {
        "datasetId": "composite_dataset_ds",
        "sources": list(download_sources),
        "download": True,
    }

    add_group_perm_to_dataset("new_custom_group", "inheritance_trio")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)
    assert len(res) == 15


def test_mixed_dataset_rights_third_party_group(
    db, user, user_client, preview_sources
):
    data = {
        "datasetId": "composite_dataset_ds",
        "sources": list(preview_sources),
    }

    add_group_perm_to_dataset("new_custom_group", "inheritance_trio")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    assert len(res) == 14


def test_mixed_dataset_rights_with_study_filters(
    db, user, user_client, preview_sources
):
    data = {
        "datasetId": "composite_dataset_ds",
        "studyFilters": [{"studyId": "quads_f1"}],
        "sources": list(preview_sources),
    }

    add_group_perm_to_dataset("new_custom_group", "inheritance_trio")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads("".join(map(lambda x: x.decode("utf-8"), res)))

    print(res)

    assert len(res) == 0

# END: Adaptive datasets rights
