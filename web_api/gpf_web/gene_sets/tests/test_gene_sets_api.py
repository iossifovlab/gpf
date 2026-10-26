# pylint: disable=W0621,C0114,C0116,W0212,W0613

import json
from typing import Any, cast
from urllib.parse import urlencode

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

from gpf.gene_sets.denovo_gene_sets_db import DenovoGeneSetsDb


def name_in_gene_sets(
    gene_sets: list[dict[str, Any]],
    name: str,
    count: int | None = None,
) -> bool:
    for gene_set in gene_sets:
        if gene_set["name"] == name:
            print(gene_set)
            if count is not None:
                return cast(bool, gene_set["count"] == count)
            return True

    return False


def test_gene_sets_collections(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_sets_collections"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    main = data[0]
    assert main["name"] == "main"
    denovo = data[1]
    assert denovo["name"] == "denovo"

    assert len(data) == 2, data


def test_denovo_gene_sets_types(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/denovo_gene_sets_types"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data[0]["datasetId"] == "t4c8_dataset"
    assert data[1]["datasetId"] == "t4c8_study_1"
    assert data[2]["datasetId"] == "t4c8_study_2"
    assert data[3]["datasetId"] == "t4c8_study_4"

    assert len(
        data[0]["personSetCollections"][0]["personSetCollectionLegend"],
    ) == 4
    assert len(
        data[1]["personSetCollections"][0]["personSetCollectionLegend"],
    ) == 2
    assert len(
        data[2]["personSetCollections"][0]["personSetCollectionLegend"],
    ) == 3
    assert len(
        data[3]["personSetCollections"][0]["personSetCollectionLegend"],
    ) == 2

    assert data[0]["personSetCollections"][0][
        "personSetCollectionLegend"
    ][0]["id"] == "autism"
    assert data[0]["personSetCollections"][0][
        "personSetCollectionLegend"
    ][1]["id"] == "epilepsy"
    assert data[0]["personSetCollections"][0][
        "personSetCollectionLegend"
    ][2]["id"] == "unaffected"
    assert data[0]["personSetCollections"][0][
        "personSetCollectionLegend"
    ][3]["id"] == "unspecified"

    assert data[1]["personSetCollections"][0][
        "personSetCollectionLegend"
    ][0]["id"] == "autism"
    assert data[1]["personSetCollections"][0][
        "personSetCollectionLegend"
    ][1]["id"] == "unaffected"


def test_denovo_gene_set_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_study_1",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism", "unaffected",
                        ],
                    },
                ],
            },
        ],
    }

    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        x.decode("utf-8") for x in response.streaming_content)  # type: ignore

    count = len([ln.strip() for ln in res.split("\n") if ln.strip()])
    assert count == 2 + 2


def test_gene_set_download_missense(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Missense",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_dataset",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism",
                        ],
                    },
                ],
            },
        ],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = "".join(
        x.decode("utf-8") for x in response.streaming_content)  # type: ignore
    count = len([ln.strip() for ln in res.split("\n") if ln.strip()])

    assert count == 2 + 1


def test_denovo_gene_set_not_found(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_dataset",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism",
                        ],
                    },
                ],
            },
        ],
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_main_gene_set_not_found(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:

    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_bad_gene_set_collection_not_found(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_gene_set_download_synonymous_autism(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_dataset",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism",
                        ],
                    },
                ],
            },
        ],
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        x.decode("utf-8") for x in response.streaming_content)  # type: ignore
    count = len([ln.strip() for ln in res.split("\n") if ln.strip()])

    assert count == 2 + 1


def test_get_gene_set_download_synonymous_recurrent(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Recurrent",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_study_4",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism",
                        ],
                    },
                ],
            },
        ],
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        x.decode("utf-8") for x in response.streaming_content)  # type: ignore
    count = len([ln.strip() for ln in res.split("\n") if ln.strip()])

    assert count == 2 + 1


def test_get_gene_set_download_synonymous_triple(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Triple",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_study_4",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism",
                        ],
                    },
                ],
            },
        ],
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        x.decode("utf-8") for x in response.streaming_content)  # type: ignore
    count = len([ln.strip() for ln in res.split("\n") if ln.strip()])

    assert count == 2 + 1


def test_get_denovo_gene_set_not_found(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_study_4",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism",
                        ],
                    },
                ],
            },
        ],
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_main_gene_set_not_found(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_bad_gene_set_collection_not_found(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_gene_set_collection_empty_query(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_set_download"
    query: dict[str, Any] = {}
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_denovo_gene_sets(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_sets"
    query = {
        "geneSetsCollection": "denovo",
        "geneSetsTypes": [
            {
                "datasetId": "t4c8_study_4",
                "collections": [
                    {
                        "personSetId": "phenotype",
                        "types": [
                            "autism",
                        ],
                    },
                ],
            },
        ],
    }
    response = admin_client.post(
        url, json.dumps(query),
        content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    assert name_in_gene_sets(result, "Synonymous", 1)


def test_gene_sets_empty_query(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_sets"
    query: dict[str, Any] = {}
    response = admin_client.post(
        url, json.dumps(query),
        content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_gene_sets_missing_collection(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument] ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_sets/gene_sets"
    query = {"geneSetsCollection": "BadBadName"}
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def _cache_family_ids(cache: Any) -> set[str]:
    if isinstance(cache, dict):
        result: set[str] = set()
        for value in cache.values():
            result |= _cache_family_ids(value)
        return result
    return set(cache)


def test_denovo_gene_sets_db_hides_family_ids(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    family_ids: set[str] = set()
    for collection in t4c8_wgpf_instance.denovo_gene_sets_db\
            ._denovo_gene_set_collections.values():
        family_ids |= _cache_family_ids(collection.cache)
    assert "f1.1" in family_ids

    response = anonymous_client.get("/api/v3/gene_sets/denovo_gene_sets_db")

    assert response.status_code == status.HTTP_200_OK
    content = response.content.decode()
    leaked = {fid for fid in family_ids if fid in content}
    assert leaked == set()


def _single_family_leaves(
    cache: Any, tokenised: Any,
) -> list[tuple[str, str]]:
    if isinstance(cache, dict):
        result = []
        for key, value in cache.items():
            result.extend(_single_family_leaves(value, tokenised[key]))
        return result
    if len(cache) == 1:
        return [(next(iter(cache)), tokenised[0])]
    return []


def test_denovo_gene_sets_db_family_token_shared_across_studies(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    collections = t4c8_wgpf_instance.denovo_gene_sets_db\
        ._denovo_gene_set_collections

    response = anonymous_client.get("/api/v3/gene_sets/denovo_gene_sets_db")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    family_tokens: dict[str, set[str]] = {}
    family_studies: dict[str, set[str]] = {}
    for study_id, collection in collections.items():
        for family_id, token in _single_family_leaves(
                collection.cache, data[study_id]["cache"]):
            family_tokens.setdefault(family_id, set()).add(token)
            family_studies.setdefault(family_id, set()).add(study_id)
    shared = {
        fid for fid, studies in family_studies.items() if len(studies) > 1
    }
    assert "f1.1" in shared
    assert {fid: family_tokens[fid] for fid in shared if
            len(family_tokens[fid]) != 1} == {}


@pytest.mark.parametrize("gene_set_id,study_ids", [
    ("Synonymous.Recurrent", ["t4c8_study_4"]),
    ("Synonymous.Recurrent",
     ["t4c8_dataset", "t4c8_study_1", "t4c8_study_2", "t4c8_study_4"]),
    ("Missense.Recurrent",
     ["t4c8_dataset", "t4c8_study_1", "t4c8_study_2", "t4c8_study_4"]),
])
def test_denovo_gene_sets_db_round_trip_keeps_recurrent_gene_sets(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    gene_set_id: str,
    study_ids: list[str],
) -> None:
    spec = {
        study_id: {"phenotype": ["autism", "unaffected"]}
        for study_id in study_ids
    }
    expected = t4c8_wgpf_instance.denovo_gene_sets_db.get_gene_set(
        gene_set_id, spec)
    assert expected is not None
    response = anonymous_client.get("/api/v3/gene_sets/denovo_gene_sets_db")
    assert response.status_code == status.HTTP_200_OK
    remote_db = DenovoGeneSetsDb(t4c8_wgpf_instance)

    remote_db.update_cache(response.json())

    assert remote_db.get_gene_set(gene_set_id, spec) == expected


def test_denovo_gene_sets_db_round_trip_counts_a_family_once(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    # Family f1.1 is the only carrier of a Missense hit in c8, in two
    # studies and in two leaves of the cache. With one token for f1.1,
    # c8 is not recurrent.
    spec = {
        study_id: {"phenotype": ["autism", "unaffected"]}
        for study_id in ["t4c8_dataset", "t4c8_study_1"]
    }
    assert t4c8_wgpf_instance.denovo_gene_sets_db.get_gene_set(
        "Missense", spec) is not None
    assert t4c8_wgpf_instance.denovo_gene_sets_db.get_gene_set(
        "Missense.Recurrent", spec) is None
    response = anonymous_client.get("/api/v3/gene_sets/denovo_gene_sets_db")
    assert response.status_code == status.HTTP_200_OK
    remote_db = DenovoGeneSetsDb(t4c8_wgpf_instance)

    remote_db.update_cache(response.json())

    assert remote_db.get_gene_set("Missense.Recurrent", spec) is None
