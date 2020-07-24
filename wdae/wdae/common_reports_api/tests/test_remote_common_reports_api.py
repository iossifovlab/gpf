from rest_framework import status


def test_remote_variant_reports(admin_client, remote_settings):
    url = "/api/v3/common_reports/studies/TEST_REMOTE_iossifov_2014"
    response = admin_client.get(url)

    assert response
    print(response)
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data


def test_remote_families_data_download(admin_client, remote_settings):
    url = "/api/v3/common_reports/families_data/TEST_REMOTE_iossifov_2014"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)
    assert streaming_content

    assert len(streaming_content) == 9450

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

    assert first_person[-1] == "iossifov_2014"
