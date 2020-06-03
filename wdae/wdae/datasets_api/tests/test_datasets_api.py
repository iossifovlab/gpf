import pytest
from box import Box

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


def test_datasets_api_get_all(admin_client):
    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200
    assert len(response.data["data"]) == 37


def test_datasets_api_get_one(admin_client):
    response = admin_client.get("/api/v3/datasets/quads_in_parent")
    print(response.data)
    assert response
    assert response.status_code == 200
    assert response.data["data"]["access_rights"] is True
    assert response.data["data"]["name"] == "QUADS_IN_PARENT"


def test_datasets_api_get_404(admin_client):
    response = admin_client.get("/api/v3/datasets/alabala")

    assert response
    assert response.status_code == 404
    assert response.data["error"] == "Dataset alabala not found"


def test_datasets_api_get_forbidden(user_client):
    response = user_client.get("/api/v3/datasets/quads_in_parent")

    assert response
    assert response.status_code == 200
    assert response.data["data"]["access_rights"] is False
    assert response.data["data"]["name"] == "QUADS_IN_PARENT"


def test_datasets_name_ordering(admin_client):
    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200

    sorted_response_data = sorted(
        response.data["data"], key=lambda d: d["name"]
    )
    assert response.data["data"] == sorted_response_data


def test_user_client_get_dataset_details(user_client, wdae_gpf_instance):
    response = user_client.get("/api/v3/datasets/details/inheritance_trio")

    assert response
    assert response.status_code == 200
    assert response.data["hasDenovo"]


def test_user_client_get_nonexistant_dataset_details(
    user_client, wdae_gpf_instance
):
    response = user_client.get("/api/v3/datasets/details/asdfghjkl")

    assert response
    assert response.status_code == 400


def test_datasets_api_get_all_with_selected_restriction(
    admin_client, mocker, wdae_gpf_instance
):
    mocker.patch.object(
        wdae_gpf_instance._variants_db,
        "dae_config",
        Box(wdae_gpf_instance._variants_db.dae_config)
    )

    mocker.patch.object(
        wdae_gpf_instance._variants_db.dae_config,
        "gpfjs",
        Box(
            wdae_gpf_instance._variants_db.dae_config.gpfjs,
            default_box=True,
            default_box_attr=None
        )
    )

    mocker.patch.object(
        wdae_gpf_instance._variants_db.dae_config.gpfjs,
        "selected_genotype_data",
        ["quads_f1", "quads_f2", "f1_group"]
    )

    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200
    assert len(response.data["data"]) == 3
