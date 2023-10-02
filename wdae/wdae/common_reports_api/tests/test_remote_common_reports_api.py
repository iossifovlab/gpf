# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from rest_framework import status  # type: ignore

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_remote_variant_reports(admin_client):
    url = "/api/v3/common_reports/studies/TEST_REMOTE_iossifov_2014"
    response = admin_client.get(url)

    assert response
    print(response)
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data


# @pytest.mark.xfail(reason="unstable test")
def test_remote_families_data_download(admin_client):
    url = "/api/v3/common_reports/families_data/TEST_REMOTE_iossifov_2014"
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)
    assert streaming_content
    assert len(streaming_content) == 44

    header = streaming_content[0].decode("utf8")
    assert header[-1] == "\n"
    header = header[:-1].split("\t")

    assert header == [
        "family_id",
        "person_id",
        "mom_id",
        "dad_id",
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
        "tag_family_type",
        "tag_family_type_full",
        # "tags"
    ]

    assert len(header) == 34

    first_person = streaming_content[1].decode("utf8")
    assert first_person[-1] == "\n"
    first_person = first_person[:-1].split("\t")
    assert len(first_person) == 34
    # assert first_person[-1] == "iossifov_2014"
