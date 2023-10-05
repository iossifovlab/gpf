# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from rest_framework import status
from django.test.client import Client

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_remote_variant_reports(admin_client: Client) -> None:
    url = "/api/v3/common_reports/studies/TEST_REMOTE_iossifov_2014"
    response = admin_client.get(url)

    assert response
    print(response)
    assert response.status_code == status.HTTP_200_OK

    data = response.data  # type: ignore
    assert data


def test_remote_families_data_download(admin_client: Client) -> None:
    url = "/api/v3/common_reports/families_data/TEST_REMOTE_iossifov_2014"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)  # type: ignore
    assert streaming_content
    assert len(streaming_content) == 45

    header = streaming_content[0].decode("utf8")
    header = header.split("\t")
    assert len(header) == 35

    assert header == [
        "familyId",
        "personId",
        "momId",
        "dadId",
        "sex",
        "status",
        "role",
        "sample_id",
        "layout",
        "generated",
        "not_sequenced",
        "missing",
        "tag_nuclear_family",
        "tag_quad_family",
        "tag_trio_family",
        "tag_simplex_family",
        "tag_multiplex_family",
        "tag_control_family",
        "tag_affected_dad_family",
        "tag_affected_mom_family",
        "tag_affected_prb_family",
        "tag_affected_sib_family",
        "tag_unaffected_dad_family",
        "tag_unaffected_mom_family",
        "tag_unaffected_prb_family",
        "tag_unaffected_sib_family",
        "tag_male_prb_family",
        "tag_female_prb_family",
        "tag_missing_mom_family",
        "tag_missing_dad_family",
        "family_bin",
        "member_index",
        # "tag_family_type",
        "tag_family_type_full",
        # "tags"
    ]

    assert len(header) == 33

    first_person = streaming_content[1].decode("utf8")
    first_person = first_person.split("\t")
    assert len(first_person) == 35
    # assert first_person[-1] == "iossifov_2014"
