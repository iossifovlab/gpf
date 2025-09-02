# pylint: disable=W0621,C0114,C0116,W0212,W0613

import copy
import json

import pandas as pd
from datasets_api.permissions import (
    add_group_perm_to_dataset,
    add_group_perm_to_user,
)
from django.contrib.auth.models import User
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

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


def test_simple_query_any_user_with_anonymous(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = anonymous_client.post(
        QUERY_VARIANTS_URL, json.dumps({"datasetId": "t4c8_study_1"}),
        content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    add_group_perm_to_dataset("any_user", "t4c8_study_1")

    response = anonymous_client.post(
        QUERY_VARIANTS_URL, json.dumps({"datasetId": "t4c8_study_1"}),
        content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK


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
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = copy.deepcopy(EXAMPLE_REQUEST)

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
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        **EXAMPLE_REQUEST,
        "download": True,
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
        "study",
        "study phenotype",
        "location",
        "variant",
        "CHROM",
        "POS",
        "REF",
        "ALT",
        "family person ids",
        "family structure",
        "family best state",
        "family genotype",
        "carrier person ids",
        "carrier person attributes",
        "inheritance type",
        "family phenotypes",
        "carrier phenotypes",
        "parents called",
        "allele frequency",
        "worst effect",
        "genes",
        "all effects",
        "effect details",
        "t4c8 score",
        "Age",
        "IQ",
    }


def test_query_summary_variants_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    query = {
        **EXAMPLE_REQUEST,
        "download": True,
    }

    response = admin_client.post(
        QUERY_VARIANTS_URL, json.dumps(query), content_type=JSON_CONTENT_TYPE,
    )
    assert response.status_code == status.HTTP_200_OK
    res = list(response.streaming_content)  # type: ignore
    assert res
    assert res[0]
    rows = [row.decode("utf-8")[:-1] for row in res]
    data = pd.DataFrame(
        [x.split("\t") for x in rows[1:3]],
        columns=rows[0].split("\t"),
    )

    assert data.to_dict(orient="list") == {
        "family id": ["f1.1", "f1.3"],
        "study": ["t4c8_study_1", "t4c8_study_1"],
        "study phenotype": ["autism", "autism"],
        "location": ["chr1:4", "chr1:4; chr1:5"],
        "variant": ["sub(T->G)", "sub(T->G); ins(A)"],
        "CHROM": ["chr1", "chr1"],
        "POS": ["4", "4"],
        "REF": ["T", "T"],
        "ALT": ["G", "G; TA"],
        "family person ids": ["mom1;dad1;p1;s1", "mom3;dad3;p3;s3"],
        "family structure": [
            "mom:F:unaffected;dad:M:unaffected;prb:F:affected;sib:M:unaffected",
            "mom:F:unaffected;dad:M:unaffected;prb:F:affected;sib:F:unaffected",
        ],
        "family best state": ["1122/1100", "1112/1000/0110"],
        "family genotype": ["0/1;0/1;0/0;0/0", "0/1;0/2;0/2;0/0"],
        "carrier person ids": ["mom1;dad1", "mom3; dad3;p3"],
        "carrier person attributes": [
            "mom:F:unaffected;dad:M:unaffected",
            "mom:F:unaffected; dad:M:unaffected;prb:F:affected",
        ],
        "inheritance type": ["mendelian", "mendelian"],
        "family phenotypes": [
            "unaffected:unaffected:autism:unaffected",
            "unaffected:unaffected:autism:unaffected",
        ],
        "carrier phenotypes": [
            "unaffected:unaffected",
            "unaffected,unaffected:autism",
        ],
        "parents called": ["4", "4"],
        "allele frequency": ["37.5", "37.5; 12.5"],
        "worst effect": ["intergenic", "intergenic"],
        "genes": ["intergenic", "intergenic"],
        "all effects": ["intergenic:intergenic", "intergenic:intergenic"],
        "effect details": [
            "intergenic:intergenic:intergenic:intergenic",
            "intergenic:intergenic:intergenic:intergenic",
        ],
        "t4c8 score": ["-", "-"],
        "Age": ["166.340", "68.001"],
        "IQ": ["104.912", "69.333"],
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
