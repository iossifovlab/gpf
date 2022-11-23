# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import json
import pytest
from rest_framework import status  # type: ignore

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_collection_configs_view(admin_client):
    url = "/api/v3/person_sets/Study1/configs"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "phenotype": {
            "domain": [
                {
                    "color": "#e35252",
                    "id": "phenotype1",
                    "name": "phenotype 1",
                    "values": ["phenotype1", ]
                },
                {
                    "color": "#b8008a",
                    "id": "phenotype2",
                    "name": "phenotype 2",
                    "values": ["phenotype2", ]
                },
                {
                    "color": "#ffffff",
                    "id": "unaffected",
                    "name": "unaffected",
                    "values": ["unaffected", ]
                },
            ],
            "id": "phenotype",
            "name": "Phenotype",
            "default": {
                "id": "unknown",
                "name": "unknown",
                "color": "#aaaaaa",
            },
            "sources": [
                {"from": "pedigree", "source": "phenotype"},
            ],
        },
        "status": {
            "domain": [
                {
                    "color": "#e35252",
                    "id": "affected",
                    "name": "affected",
                    "values": ["affected", ]
                },
                {
                    "color": "#ffffff",
                    "id": "unaffected",
                    "name": "unaffected",
                    "values": ["unaffected", ]
                }
            ],
            "default": {
                "id": "unspecified",
                "name": "unspecified",
                "color": "#aaaaaa",
            },
            "id": "status",
            "name": "Affected Status",
            "sources": [{"from": "pedigree", "source": "status"}],
        }
    }


def test_get_person_sets_collection_stats(admin_client):
    url = "/api/v3/person_sets/Study1/stats/phenotype"
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.data == {
        "phenotype1": {
            "parents": 4,
            "children": 12,
        },
        "phenotype2": {
            "parents": 0,
            "children": 4,
        },
        "unaffected": {
            "parents": 8,
            "children": 1,
        },
        "unknown": {
            "parents": 4,
            "children": 0,
        }
    }


def test_get_person_sets_collection_stats_nonexistent(admin_client):
    response = admin_client.get(
        "/api/v3/person_sets/nonexistentstudy/stats/status"
    )
    assert response.status_code == 404
    response = admin_client.get(
        "/api/v3/person_sets/Study1/stats/nonexistentcollection"
    )
    assert response.status_code == 404


def test_get_person_sets_collection_stats_no_id(admin_client):
    response = admin_client.get(
        "/api/v3/person_sets/Study1/stats"
    )
    assert response.status_code == 404
