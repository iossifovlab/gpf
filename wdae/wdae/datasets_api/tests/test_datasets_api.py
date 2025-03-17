# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

from datasets_api.permissions import add_group_perm_to_dataset


def test_datasets_api_get_all(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5


def test_datasets_api_get_one(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/t4c8_study_1")
    assert response
    assert response.status_code == 200

    data = response.json()

    assert data["data"]["access_rights"] is True
    assert data["data"]["name"] == "t4c8_study_1"


def test_datasets_default_description_editable(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/t4c8_study_1")
    assert response
    assert response.status_code == 200

    data = response.json()
    assert data["data"]["name"] == "t4c8_study_1"
    assert data["data"]["description_editable"] is True


def test_datasets_api_get_404(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/alabala")

    assert response
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "Dataset alabala not found"


def test_datasets_api_get_forbidden(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = user_client.get("/api/v3/datasets/t4c8_study_1")

    assert response
    assert response.status_code == 200

    data = response.json()
    assert data["data"]["name"] == "t4c8_study_1"
    assert data["data"]["access_rights"] is False


def test_user_client_get_nonexistant_dataset_details(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = user_client.get("/api/v3/datasets/details/alabala")

    assert response
    assert response.status_code == 404


def test_datasets_api_parents(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:

    response = admin_client.get("/api/v3/datasets/t4c8_study_1")
    assert response
    assert response.status_code == 200

    data = response.json()
    assert "parents" in data["data"]
    assert data["data"]["parents"] == ["t4c8_dataset"]


def test_datasets_pedigree_no_such_dataset(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/pedigree/alabala/col")
    assert response
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert data["error"] == "Dataset alabala not found"


def test_datasets_pedigree_no_such_column(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        "/api/v3/datasets/pedigree/t4c8_study_1/alabala")
    assert response
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert data["error"] == "No such column alabala"


def test_datasets_pedigree_proper_request(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        "/api/v3/datasets/pedigree/t4c8_study_1/phenotype")
    assert response
    assert response.status_code == 200

    data = response.json()
    assert "column_name" in data
    assert "values_domain" in data
    assert data["column_name"] == "phenotype"
    assert set(data["values_domain"]) == {
        "unaffected", "autism",
    }


def test_datasets_config_no_such_dataset(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/config/alabala")
    assert response
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert data["error"] == "Dataset alabala not found"


def test_datasets_config_proper_request(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/config/t4c8_study_1")
    assert response
    assert response.status_code == 200

    data = response.json()
    assert data


def test_datasets_description_not_admin(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = user_client.post("/api/v3/datasets/description/t4c8_study_1")
    assert response
    assert response.status_code == 403

    data = response.json()
    assert "error" in data
    assert data["error"] == \
        "You have no permission to edit the description."


def test_datasets_description_get(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get(
        "/api/v3/datasets/description/t4c8_study_1",
    )
    assert response
    assert response.status_code == 200

    data = response.json()
    assert data["description"] is None


def test_datasets_description_post(
    admin_client: Client,
    t4c8_wgpf: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/datasets/description/t4c8_study_1"
    args = {
        "description": "some new description",
    }
    response = admin_client.post(
        url, json.dumps(args), content_type="application/json", format="json",
    )
    assert response
    assert response.status_code == 200

    response = admin_client.get(
        "/api/v3/datasets/description/t4c8_study_1",
    )
    assert response
    assert response.status_code == 200

    data = response.json()
    assert data["description"] == "some new description"


def test_datasets_hierarchy(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/hierarchy/")
    assert response
    assert response.status_code == 200

    data = response.json()
    assert data
    assert len(data["data"]) == 3

    dataset = data["data"][0]
    assert dataset == {
        "dataset": "t4c8_dataset",
        "children": [
            {"dataset": "t4c8_study_1",
             "children": None,
             "name": "t4c8_study_1",
             "access_rights": True},
            {"dataset": "t4c8_study_2",
             "children": None,
             "name": "t4c8_study_2",
             "access_rights": True},
        ],
        "name": "t4c8_dataset",
        "access_rights": True,
    }


def test_datasets_hierarchy_hidden(
    user_client: Client,
    custom_wgpf: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = user_client.get("/api/v3/datasets/hierarchy/")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 4

    add_group_perm_to_dataset("hidden", "omni_dataset")
    response = user_client.get("/api/v3/datasets/hierarchy/")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 3


def test_datasets_permissions(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions")

    data = response.json()

    assert len(data) == 5
    assert set(data[0].keys()) == {
        "dataset_id",
        "dataset_name",
        "broken",
        "users",
        "groups",
    }

    response = admin_client.get("/api/v3/datasets/permissions?page=2")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_datasets_permissions_single(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions/t4c8_study_1")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert set(data.keys()) == {
        "dataset_id",
        "dataset_name",
        "broken",
        "users",
        "groups",
    }


def test_datasets_permissions_single_missing(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions/alabala")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_datasets_permissions_search(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions?search=set")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["dataset_id"] == "t4c8_dataset"


def test_datasets_permissions_search_nonexistent(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions?search=alabala")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_datasets_api_visible_datasets(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = admin_client.get("/api/v3/datasets/visible")
    assert response
    assert response.status_code == 200

    data = response.json()
    assert data == ["t4c8_dataset", "t4c8_study_1"]
