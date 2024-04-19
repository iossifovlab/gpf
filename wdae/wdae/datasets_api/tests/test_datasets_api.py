# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from pprint import pprint

import pytest
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status  # type: ignore

from dae.configuration.gpf_config_parser import FrozenBox

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_datasets_api_get_all(admin_client: Client) -> None:
    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200
    data = response.data  # type: ignore
    assert len(data["data"]) == 39


def test_datasets_api_get_all_studies(admin_client: Client) -> None:
    response = admin_client.get("/api/v3/datasets/studies")

    assert response
    assert response.status_code == 200
    data = response.data  # type: ignore
    assert len(data["data"]) == 21


def test_datasets_api_get_one(admin_client: Client) -> None:
    response = admin_client.get("/api/v3/datasets/quads_in_parent")
    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore

    assert data["data"]["access_rights"] is True
    assert data["data"]["name"] == "QUADS_IN_PARENT"


def test_datasets_default_description_editable(admin_client: Client) -> None:
    response = admin_client.get("/api/v3/datasets/quads_in_parent")
    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert data["data"]["description_editable"] is True
    assert data["data"]["name"] == "QUADS_IN_PARENT"


def test_datasets_api_get_404(admin_client: Client) -> None:
    response = admin_client.get("/api/v3/datasets/alabala")

    assert response
    assert response.status_code == 404

    data = response.data  # type: ignore
    assert data["error"] == "Dataset alabala not found"


def test_datasets_api_get_dataset_with_hierarchy_description(
    admin_client: Client
) -> None:
    response = admin_client.get("/api/v3/datasets/Dataset1")

    assert response
    data = response.data  # type: ignore
    assert data["data"]["children_description"] == (
        "\nThis dataset includes:\n"
        "- **[Study1](Study1)** some new description\n\n"
        "- **[Study3](Study3)** \n"
    )


def test_datasets_api_get_forbidden(user_client: Client) -> None:
    response = user_client.get("/api/v3/datasets/quads_in_parent")

    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert data["data"]["access_rights"] is False
    assert data["data"]["name"] == "QUADS_IN_PARENT"


def test_user_client_get_dataset_details(
    user_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = user_client.get("/api/v3/datasets/details/inheritance_trio")

    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert data["hasDenovo"]


def test_user_client_get_nonexistant_dataset_details(
    user_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = user_client.get("/api/v3/datasets/details/asdfghjkl")

    assert response
    assert response.status_code == 404


def test_datasets_api_parents(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:

    dataset1_wrapper = wdae_gpf_instance.get_wdae_wrapper("Dataset1")
    assert dataset1_wrapper is not None
    assert dataset1_wrapper.is_group

    # study1 = wdae_gpf_instance.get_genotype_data("Study1")
    # assert "Dataset1" in study1.parents

    response = admin_client.get("/api/v3/datasets/Study1")
    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert "parents" in data["data"]
    assert data["data"]["parents"] == ["Dataset1"]


def test_datasets_pedigree_no_such_dataset(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/pedigree/alabala/col")
    assert response
    assert response.status_code == 404

    data = response.data  # type: ignore
    assert "error" in data
    assert data["error"] == "Dataset alabala not found"


def test_datasets_pedigree_no_such_column(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/pedigree/Study1/alabala")
    assert response
    assert response.status_code == 404

    data = response.data  # type: ignore
    assert "error" in data
    assert data["error"] == "No such column alabala"


def test_datasets_pedigree_proper_request(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/pedigree/Study1/phenotype")
    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert "column_name" in data and \
           "values_domain" in data
    assert data["column_name"] == "phenotype"
    assert set(data["values_domain"]) == {
        "unaffected", "phenotype1", "phenotype2", "pheno",
    }


def test_datasets_config_no_such_dataset(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/config/alabala")
    assert response
    assert response.status_code == 404

    data = response.data  # type: ignore
    assert "error" in data
    assert data["error"] == "Dataset alabala not found"


def test_datasets_config_proper_request(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/config/Study1")
    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert data


def test_datasets_description_not_admin(
    user_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = user_client.post("/api/v3/datasets/description/Study1")
    assert response
    assert response.status_code == 403

    data = response.data  # type: ignore
    assert "error" in data
    assert data["error"] == \
        "You have no permission to edit the description."


def test_datasets_description_get(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/description/Study1")
    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert data["description"] == "some new description"


def test_datasets_description_post(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    url = "/api/v3/datasets/description/Study1"
    args = {
        "description": "some new description",
    }
    response = admin_client.post(
        url, json.dumps(args), content_type="application/json", format="json",
    )
    assert response
    assert response.status_code == 200


def test_datasets_hierarchy(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/hierarchy/")
    assert response
    assert response.status_code == 200

    data = response.data  # type: ignore
    assert data
    pprint(data)
    assert len(data["data"]) == 22
    dataset1 = next(filter(
        lambda x: x["dataset"] == "Dataset1", data["data"],
    ))
    assert dataset1 == {
        "dataset": "Dataset1",
        "children": [
            {"dataset": "Study1",
             "children": None,
             "name": "Study1",
             "access_rights": True},
            {"dataset": "Study3",
             "children": None,
             "name": "Study3",
             "access_rights": True},
        ],
        "name": "Dataset1",
        "access_rights": True,
    }


def test_datasets_permissions(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions")

    data = response.data  # type: ignore
    assert len(data) == 25
    assert set(data[0].keys()) == set([
        "dataset_id",
        "dataset_name",
        "broken",
        "users",
        "groups",
    ])

    response = admin_client.get("/api/v3/datasets/permissions?page=2")

    data = response.data  # type: ignore
    assert len(data) == 14

    response = admin_client.get("/api/v3/datasets/permissions?page=3")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_datasets_permissions_single(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions/Dataset1")
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert set(data.keys()) == set([
        "dataset_id",
        "dataset_name",
        "broken",
        "users",
        "groups",
    ])


def test_datasets_permissions_single_missing(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions/alabala")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_datasets_permissions_search(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    response = admin_client.get("/api/v3/datasets/permissions?search=set1")

    data = response.data  # type: ignore
    assert len(data) == 1
    assert data[0]["dataset_id"] == "Dataset1"


def test_datasets_api_visible_datasets(
    admin_client: Client, wdae_gpf_instance: WGPFInstance,
) -> None:
    # FIXME This is a temporary hack to mock the
    # dae_config of wdae_gpf_instance since using the mocker
    # fixture does not work.
    old_conf = wdae_gpf_instance.dae_config
    edited_conf = old_conf.to_dict()
    edited_conf["gpfjs"]["visible_datasets"] = [
        "quads_f1", "quads_f2", "f1_group", "nonexistent",
    ]
    wdae_gpf_instance.dae_config = FrozenBox(edited_conf)

    try:
        response = admin_client.get("/api/v3/datasets/visible")
        assert response and response.status_code == 200

        data = response.data  # type: ignore
        assert data == ["quads_f1", "quads_f2", "f1_group"]
    finally:
        wdae_gpf_instance.dae_config = old_conf
