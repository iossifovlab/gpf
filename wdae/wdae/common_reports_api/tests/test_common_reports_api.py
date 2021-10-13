import pytest

from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets", "use_common_reports"
)


def test_variant_reports(admin_client):
    url = "/api/v3/common_reports/studies/study4"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data


def test_variant_reports_no_permissions(user_client):
    url = "/api/v3/common_reports/studies/study4"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN

    data = response.data
    assert data


@pytest.mark.xfail(reason="this test is flipping; should be investigated")
def test_variant_reports_not_found(admin_client):
    url = "/api/v3/common_reports/studies/Study3"
    response = admin_client.get(url)

    assert response
    assert response.data["error"] == "Common report Study3 not found"
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_families_data_download(admin_client):
    url = "/api/v3/common_reports/families_data/Study1"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)
    assert streaming_content

    assert len(streaming_content) == 31

    header = streaming_content[0].decode("utf8")
    assert header[-1] == "\n"
    header = header[:-1].split("\t")
    assert len(header) == 8

    assert header == [
        "familyId",
        "personId",
        "dadId",
        "momId",
        "sex",
        "status",
        "role",
        "genotype_data_study",
    ]

    first_person = streaming_content[1].decode("utf8")
    assert first_person[-1] == "\n"
    first_person = first_person[:-1].split("\t")
    assert len(first_person) == 8

    assert first_person[-1] == "Study1"


@pytest.mark.xfail(reason="this test is flipping; should be investigated")
def test_families_data_download_no_permissions(user_client):
    url = "/api/v3/common_reports/families_data/study4"
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN
