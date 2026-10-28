# pylint: disable=W0621,C0114,C0116,W0212,W0613
import csv
import json

import pytest
import pytest_mock
from django.http import StreamingHttpResponse
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

STUDY_1_FAMILIES = {"f1.1", "f1.3"}
STUDY_2_FAMILIES = {"f2.1", "f2.3"}
STUDY_1_ONLY_PERSONS = {"p1", "s1", "p3", "s3"}


def _counter_families(client: Client, counter_id: int) -> set[str]:
    response = client.post(
        "/api/v3/common_reports/family_counters",
        json.dumps({
            "study_id": "t4c8_dataset",
            "group_name": "Phenotype",
            "counter_id": str(counter_id),
        }),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    return set(response.data)  # type: ignore


def _tsv_rows(response: StreamingHttpResponse) -> list[dict[str, str]]:
    assert response.status_code == status.HTTP_200_OK
    lines = b"".join(response.streaming_content).decode()  # type: ignore
    return list(csv.DictReader(lines.splitlines(), delimiter="\t"))


def _counter_download(client: Client, counter_id: int) -> list[dict[str, str]]:
    response = client.post(
        "/api/v3/common_reports/family_counters/download",
        json.dumps({
            "queryData": json.dumps({
                "study_id": "t4c8_dataset",
                "group_name": "Phenotype",
                "counter_id": str(counter_id),
            }),
        }),
        content_type="application/json",
    )
    return _tsv_rows(response)  # type: ignore


def _families_data_get(client: Client) -> list[dict[str, str]]:
    return _tsv_rows(client.get(  # type: ignore
        "/api/v3/common_reports/families_data/t4c8_dataset"))


def _families_data_post(client: Client) -> list[dict[str, str]]:
    return _tsv_rows(client.post(  # type: ignore
        "/api/v3/common_reports/families_data/t4c8_dataset",
        json.dumps({
            "tagsQuery": {
                "orMode": True,
                "includeTags": ["tag_nuclear_family"],
                "excludeTags": [],
            },
        }),
        content_type="application/json",
    ))


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_family_counters_under_partial_grant(
    user_client: Client,
) -> None:
    families = set().union(*(
        _counter_families(user_client, counter_id)
        for counter_id in range(4)
    ))

    assert families == STUDY_2_FAMILIES


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_family_counters_under_full_grant(
    user_client: Client,
) -> None:
    families = set().union(*(
        _counter_families(user_client, counter_id)
        for counter_id in range(4)
    ))

    assert families == STUDY_1_FAMILIES | STUDY_2_FAMILIES


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_family_counters_download_under_partial_grant(
    user_client: Client,
) -> None:
    rows = [
        row
        for counter_id in range(4)
        for row in _counter_download(user_client, counter_id)
    ]

    assert {row["familyId"] for row in rows} == STUDY_2_FAMILIES
    assert {row["personId"] for row in rows} & STUDY_1_ONLY_PERSONS == set()


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_family_counters_download_under_full_grant(
    user_client: Client,
) -> None:
    rows = [
        row
        for counter_id in range(4)
        for row in _counter_download(user_client, counter_id)
    ]

    assert {row["familyId"] for row in rows} == (
        STUDY_1_FAMILIES | STUDY_2_FAMILIES)


@pytest.mark.parametrize("download", [_families_data_get, _families_data_post])
@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_families_data_under_partial_grant(
    user_client: Client,
    download: object,
) -> None:
    rows = download(user_client)  # type: ignore

    assert {row["familyId"] for row in rows} == STUDY_2_FAMILIES
    assert {row["personId"] for row in rows} & STUDY_1_ONLY_PERSONS == set()


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_families_data_query_data_form_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.post(
        "/api/v3/common_reports/families_data/t4c8_dataset",
        json.dumps({
            "queryData": json.dumps({
                "tagsQuery": {
                    "orMode": True,
                    "includeTags": ["tag_trio_family"],
                    "excludeTags": [],
                },
            }),
        }),
        content_type="application/json",
    )

    rows = _tsv_rows(response)  # type: ignore

    assert {row["familyId"] for row in rows} == {"f2.1"}


@pytest.mark.parametrize("download", [_families_data_get, _families_data_post])
@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_families_data_under_full_grant(
    user_client: Client,
    download: object,
) -> None:
    rows = download(user_client)  # type: ignore

    assert {row["familyId"] for row in rows} == (
        STUDY_1_FAMILIES | STUDY_2_FAMILIES)
    assert {row["personId"] for row in rows} >= STUDY_1_ONLY_PERSONS


@pytest.mark.usefixtures("partial_grant", "t4c8_wgpf_instance")
def test_full_variant_report_under_partial_grant_is_forbidden(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/common_reports/studies/t4c8_dataset/full")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.usefixtures("full_grant", "t4c8_wgpf_instance")
def test_full_variant_report_under_full_grant(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/common_reports/studies/t4c8_dataset/full")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("url", [
    "/api/v3/common_reports/families_data/t4c8_dataset",
])
@pytest.mark.usefixtures("partial_grant")
def test_families_data_of_a_remote_child_under_partial_grant_is_forbidden(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: pytest_mock.MockFixture,
    url: str,
) -> None:
    study = t4c8_wgpf_instance.get_genotype_data("t4c8_study_2")
    mocker.patch.object(study, "is_remote", new=True)

    response = user_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.usefixtures("all_children_grant", "t4c8_wgpf_instance")
def test_full_variant_report_under_grant_on_all_child_studies(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/common_reports/studies/t4c8_dataset/full")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("download", [_families_data_get, _families_data_post])
@pytest.mark.usefixtures("all_children_grant", "t4c8_wgpf_instance")
def test_families_data_under_grant_on_all_child_studies(
    user_client: Client,
    download: object,
) -> None:
    rows = download(user_client)  # type: ignore

    assert {row["familyId"] for row in rows} == (
        STUDY_1_FAMILIES | STUDY_2_FAMILIES)
