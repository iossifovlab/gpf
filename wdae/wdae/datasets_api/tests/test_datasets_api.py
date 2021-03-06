import pytest
from dae.configuration.gpf_config_parser import FrozenBox

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance", "calc_gene_sets")


def test_datasets_api_get_all(admin_client):
    response = admin_client.get("/api/v3/datasets")

    assert response
    assert response.status_code == 200
    assert len(response.data["data"]) == 40


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
    admin_client, wdae_gpf_instance
):
    # FIXME This is a temporary hack to mock the
    # dae_config of wdae_gpf_instance since using the mocker
    # fixture does not work.
    old_conf = wdae_gpf_instance.dae_config
    edited_conf = old_conf.to_dict()
    edited_conf["gpfjs"]["selected_genotype_data"] = [
        "quads_f1", "quads_f2", "f1_group"
    ]
    wdae_gpf_instance.dae_config = FrozenBox(edited_conf)

    try:
        response = admin_client.get("/api/v3/datasets")
        assert response
        assert response.status_code == 200
        assert len(response.data["data"]) == 3
    finally:
        wdae_gpf_instance.dae_config = old_conf


def test_datasets_api_parents(admin_client, wdae_gpf_instance):

    dataset1_wrapper = wdae_gpf_instance.get_wdae_wrapper("Dataset1")
    assert dataset1_wrapper is not None
    assert dataset1_wrapper.is_group

    # study1 = wdae_gpf_instance.get_genotype_data("Study1")
    # assert "Dataset1" in study1.parents

    response = admin_client.get("/api/v3/datasets/Study1")
    assert response
    assert response.status_code == 200
    print(response.data)
    data = response.data["data"]

    assert "parents" in data
    assert data["parents"] == ["Dataset1"]
