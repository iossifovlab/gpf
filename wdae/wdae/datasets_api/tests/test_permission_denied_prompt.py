# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
from django.test import Client


def test_permission_denied_prompt(user_client: Client) -> None:
    response = user_client.get("/api/v3/datasets/denied_prompt")

    assert response
    assert response.status_code == 200
    assert response.json()["data"] == (
        "The whole Genotype and Phenotype in Families (GPF) data and"
        " functionalities are accessible only by registered users."
        " Visit the About page for information how to register."
    )
