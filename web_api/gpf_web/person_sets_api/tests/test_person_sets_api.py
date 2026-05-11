# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


def test_collection_configs_view(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/person_sets/t4c8_study_1/configs"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {  # type: ignore
        "phenotype": {
            "domain": [
                {
                    "id": "autism",
                    "name": "autism",
                    "values": ("affected", ),
                    "color": "#ff2121",
                },
                {
                    "id": "unaffected",
                    "name": "unaffected",
                    "values": ("unaffected", ),
                    "color": "#ffffff",
                },
            ],
            "id": "phenotype",
            "name": "Phenotype",
            "default": {
                "id": "unspecified",
                "name": "unspecified",
                "color": "#aaaaaa",
            },
            "sources": [
                {"from": "pedigree", "source": "status"},
            ],
        },
    }


def test_collection_domain_view(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/person_sets/t4c8_study_1/domain"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {  # type: ignore
        "phenotype": {
            "domain": [
                {
                    "id": "autism",
                    "name": "autism",
                    "color": "#ff2121",
                },
                {
                    "id": "unaffected",
                    "name": "unaffected",
                    "color": "#ffffff",
                },
            ],
            "id": "phenotype",
            "name": "Phenotype",
        },
    }


def test_get_person_sets_collection_stats(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/person_sets/t4c8_study_1/stats/phenotype"
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.data == {  # type: ignore
        "autism": {
            "parents": 0,
            "children": 2,
        },
        "unaffected": {
            "parents": 0,
            "children": 2,
        },
    }


def test_get_person_sets_collection_stats_nonexistent(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        "/api/v3/person_sets/nonexistentstudy/stats/status",
    )
    assert response.status_code == 404
    response = admin_client.get(
        "/api/v3/person_sets/t4c8_study_1/stats/nonexistentcollection",
    )
    assert response.status_code == 404


def test_get_person_sets_collection_stats_no_id(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        "/api/v3/person_sets/t4c8_study_1/stats",
    )
    assert response.status_code == 404
