# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
from django.test import Client

from dae.gpf_instance.gpf_instance import GPFInstance


def test_permission_denied_prompt_through_user_client(
    user_client: Client,
    wdae_gpf_instance: GPFInstance,
) -> None:
    response = user_client.get("/api/v3/datasets/denied_prompt")

    assert response
    assert response.status_code == 200
    assert response.json()["data"] == (
        "This is a real permission denied prompt."
        " The view has successfully sent the prompt.\n"
    )


def test_default_permission_denied_prompt(user_client: Client) -> None:
    response = user_client.get("/api/v3/datasets/denied_prompt")

    assert response
    assert response.status_code == 200
    assert response.json()["data"] == (
        "The Genotype and Phenotype in Families (GPF) data is accessible by "
        + "registered users. Contact the system administrator of the "
        + "GPF system to get an account in the system and get permission "
        + "to access the data."
    )
