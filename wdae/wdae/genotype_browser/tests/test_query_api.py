# pylint: disable=W0621,C0114,C0116,W0212,W0613

import copy
import json

import pytest
from datasets_api.permissions import (
    add_group_perm_to_dataset,
    add_group_perm_to_user,
)
from django.contrib.auth.models import User
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


EXAMPLE_REQUEST: dict = {
    "datasetId": "t4c8_study_1",
}


QUERY_VARIANTS_URL = "/api/v3/genotype_browser/query"
JSON_CONTENT_TYPE = "application/json"


def test_simple_query(
    admin_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = copy.deepcopy(EXAMPLE_REQUEST)
    data["sources"] = list(preview_sources)

    response = admin_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )

    assert response.status_code == status.HTTP_200_OK
    res = json.loads(
        "".join(x.decode("utf-8") for x in response.streaming_content))  # type: ignore

    assert len(res) == 12


def test_simple_query_download_anonymous(
    anonymous_client: Client,
    download_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        **EXAMPLE_REQUEST,
        "download": True,
        "sources": download_sources,
    }
    response = anonymous_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_simple_query_download(
    admin_client: Client,
    download_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        **EXAMPLE_REQUEST,
        "download": True,
        "sources": download_sources,
    }

    response = admin_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)  # type: ignore
    assert res
    assert res[0]
    header = res[0].decode("utf-8")[:-1].split("\t")

    assert len(res) == 13

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
    admin_client: Client,
    summary_preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = copy.deepcopy(EXAMPLE_REQUEST)
    data["sources"] = list(summary_preview_sources)

    response = admin_client.post(
        QUERY_VARIANTS_URL,
        json.dumps(data),
        content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 12


def test_simple_query_summary_variants_download(
    admin_client: Client,
    summary_download_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        **EXAMPLE_REQUEST,
        "download": True,
        "sources": summary_download_sources,
    }

    response = admin_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)  # type: ignore
    assert res
    assert res[0]
    header = res[0].decode("utf-8")[:-1].split("\t")

    assert len(res) == 13

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


def test_missing_dataset(
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = copy.deepcopy(EXAMPLE_REQUEST)
    data["sources"] = list(preview_sources)
    del data["datasetId"]

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert status.HTTP_400_BAD_REQUEST, response.status_code


def test_bad_dataset(
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = copy.deepcopy(EXAMPLE_REQUEST)
    data["sources"] = list(preview_sources)
    data["datasetId"] = "ala bala portokala"

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert status.HTTP_400_BAD_REQUEST, response.status_code


# START: Adaptive datasets rights
def test_normal_dataset_rights_query(
    user: User,
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "sources": list(preview_sources),
    }

    add_group_perm_to_user("t4c8_dataset", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 17


def test_mixed_dataset_rights_query(
    user: User,
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "sources": list(preview_sources),
    }

    add_group_perm_to_user("t4c8_study_1", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 12


def test_mixed_layered_dataset_rights_query(
    user: User,
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "sources": list(preview_sources),
    }

    add_group_perm_to_user("t4c8_study_1", user)
    add_group_perm_to_user("t4c8_dataset", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 17


def test_mixed_layered_diff_group_dataset_rights_query(
    user: User,
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "sources": list(preview_sources),
    }

    add_group_perm_to_dataset("new_custom_group", "t4c8_dataset")
    add_group_perm_to_dataset("new_custom_group", "t4c8_study_1")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 17


def test_mixed_dataset_rights_download(
    user: User,
    user_client: Client,
    download_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "sources": list(download_sources),
        "download": True,
    }

    add_group_perm_to_dataset("new_custom_group", "t4c8_study_1")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)  # type: ignore
    assert len(res) == 13


def test_mixed_dataset_rights_third_party_group(
    user: User,
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "sources": list(preview_sources),
    }

    add_group_perm_to_dataset("new_custom_group", "t4c8_study_1")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 12


def test_mixed_dataset_rights_with_study_filters(
    user: User,
    user_client: Client,
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_dataset",
        "studyFilters": [{"studyId": "t4c8_study_2"}],
        "sources": list(preview_sources),
    }

    add_group_perm_to_dataset("new_custom_group", "t4c8_study_1")
    add_group_perm_to_user("new_custom_group", user)

    response = user_client.post(
        QUERY_VARIANTS_URL, json.dumps(data), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = response.streaming_content  # type: ignore
    res = json.loads("".join(x.decode("utf-8") for x in res))

    assert len(res) == 0

# END: Adaptive datasets rights
