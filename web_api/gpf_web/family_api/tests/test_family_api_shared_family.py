# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Two child studies of one dataset share the family id ``fs``."""
import csv
import json
import pathlib

import pytest
import pytest_mock
from datasets_api.permissions import add_group_perm_to_user
from django.contrib.auth.models import User
from django.test.client import Client
from gain.genomic_resources.testing import setup_pedigree, setup_vcf
from gpf_instance.gpf_instance import WGPFInstance, reload_datasets
from rest_framework import status
from utils.testing import setup_wgpf_instance

from gpf.testing.import_helpers import setup_dataset_config, vcf_study


def _shared_family_study(
    root_path: pathlib.Path,
    instance: WGPFInstance,
    study_id: str,
    child_id: str,
) -> None:
    ped_path = setup_pedigree(
        root_path / study_id / "pedigree" / "in.ped",
        f"""
familyId personId dadId momId sex status role
fs       mom      0     0     2   1      mom
fs       dad      0     0     1   1      dad
fs       {child_id}      dad   mom   2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / study_id / "vcf" / "in.vcf.gz",
        f"""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom dad {child_id}
chr1   5   .  A   C   .    .      .    GT     0/0 0/0 0/1
        """)
    vcf_study(
        root_path, study_id, ped_path, [vcf_path], gpf_instance=instance,
    )


@pytest.fixture(scope="module")
def shared_family_module(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("shared_family")
    instance = setup_wgpf_instance(root_path)
    _shared_family_study(root_path, instance, "shared_study_a", "ch_a")
    _shared_family_study(root_path, instance, "shared_study_b", "ch_b")
    _shared_family_study(root_path, instance, "shared_study_c", "ch_c")
    setup_dataset_config(
        instance, "shared_dataset",
        ["shared_study_a", "shared_study_b", "shared_study_c"])
    instance.reload()
    return instance


@pytest.fixture
def shared_family_instance(
    shared_family_module: WGPFInstance,
    db: None,  # ruff: ignore[unused-function-argument]
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    reload_datasets(shared_family_module)
    for target in (
        "gpf_instance.gpf_instance.get_wgpf_instance",
        "datasets_api.permissions.get_wgpf_instance",
        "query_base.query_base.get_wgpf_instance",
    ):
        mocker.patch(target, return_value=shared_family_module)
    return shared_family_module


@pytest.fixture
def grant_on_study_b(user: User) -> User:
    add_group_perm_to_user("shared_study_b", user)
    return user


@pytest.mark.usefixtures("shared_family_instance")
def test_dataset_merges_the_shared_family(
    admin_client: Client,
) -> None:
    response = admin_client.get("/api/v3/families/shared_dataset/fs/members")

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "mom", "dad", "ch_a", "ch_b", "ch_c",
    }


@pytest.mark.usefixtures("grant_on_study_b", "shared_family_instance")
@pytest.mark.parametrize("url", [
    "/api/v3/families/shared_dataset/fs",
    "/api/v3/families/shared_dataset/fs/members",
    "/api/v3/families/shared_dataset/fs/members/all",
    "/api/v3/families/shared_dataset/all",
])
def test_shared_family_shows_members_of_allowed_study(
    user_client: Client,
    url: str,
) -> None:
    response = user_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    content = response.content.decode()
    assert "ch_b" in content
    assert "ch_a" not in content
    assert "ch_c" not in content


@pytest.mark.usefixtures("grant_on_study_b", "shared_family_instance")
def test_member_of_allowed_study_in_shared_family(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/families/shared_dataset/fs/members/ch_b")

    assert response.status_code == status.HTTP_200_OK
    assert "ch_b" in response.content.decode()


@pytest.mark.usefixtures("grant_on_study_b", "shared_family_instance")
def test_member_of_other_study_in_shared_family_is_404(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/families/shared_dataset/fs/members/ch_a")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.fixture
def grant_on_all_shared_studies(user: User) -> User:
    for study_id in ("shared_study_a", "shared_study_b", "shared_study_c"):
        add_group_perm_to_user(study_id, user)
    return user


@pytest.fixture
def grant_on_studies_a_and_b(user: User) -> User:
    add_group_perm_to_user("shared_study_a", user)
    add_group_perm_to_user("shared_study_b", user)
    return user


@pytest.mark.usefixtures("grant_on_studies_a_and_b", "shared_family_instance")
def test_shared_family_merges_members_of_two_allowed_studies(
    user_client: Client,
) -> None:
    response = user_client.get("/api/v3/families/shared_dataset/fs/members")

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "mom", "dad", "ch_a", "ch_b",
    }


@pytest.mark.usefixtures("grant_on_studies_a_and_b", "shared_family_instance")
def test_collection_stats_count_children_of_two_allowed_studies(
    user_client: Client,
) -> None:
    response = user_client.get(
        "/api/v3/person_sets/shared_dataset/stats/phenotype")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["autism"]["children"] == 2


def _families_data_rows(
    client: Client, tags_query: dict | None = None,
) -> list[dict[str, str]]:
    url = "/api/v3/common_reports/families_data/shared_dataset"
    if tags_query is None:
        response = client.get(url)
    else:
        response = client.post(
            url, json.dumps({"tagsQuery": tags_query}),
            content_type="application/json")
    assert response.status_code == status.HTTP_200_OK
    content = b"".join(response.streaming_content).decode()  # type: ignore
    return list(csv.DictReader(content.splitlines(), delimiter="\t"))


MULTIPLEX = {
    "orMode": True,
    "includeTags": ["tag_multiplex_family"],
    "excludeTags": [],
}


@pytest.mark.usefixtures("grant_on_study_b", "shared_family_instance")
def test_families_data_shows_members_of_allowed_study(
    user_client: Client,
) -> None:
    rows = _families_data_rows(user_client)

    assert {row["personId"] for row in rows} == {"mom", "dad", "ch_b"}


@pytest.mark.usefixtures("shared_family_instance")
def test_merged_shared_family_is_multiplex(
    admin_client: Client,
) -> None:
    rows = _families_data_rows(admin_client, MULTIPLEX)

    assert {row["familyId"] for row in rows} == {"fs"}


@pytest.mark.usefixtures("grant_on_study_b", "shared_family_instance")
def test_families_data_tags_query_uses_members_of_allowed_study(
    user_client: Client,
) -> None:
    rows = _families_data_rows(user_client, MULTIPLEX)

    assert not rows


def _counter_families(client: Client) -> list[str]:
    response = client.post(
        "/api/v3/common_reports/family_counters",
        json.dumps({
            "study_id": "shared_dataset",
            "group_name": "Phenotype",
            "counter_id": "0",
        }),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    return list(response.data)  # type: ignore


@pytest.mark.usefixtures("shared_family_instance")
def test_family_counter_of_the_merged_shared_family(
    admin_client: Client,
) -> None:
    assert _counter_families(admin_client) == ["fs"]


@pytest.mark.usefixtures("grant_on_study_b", "shared_family_instance")
def test_family_counters_leave_out_a_partly_granted_family(
    user_client: Client,
) -> None:
    assert not _counter_families(user_client)


def _counter_download_families(client: Client) -> set[str]:
    response = client.post(
        "/api/v3/common_reports/family_counters/download",
        json.dumps({
            "queryData": json.dumps({
                "study_id": "shared_dataset",
                "group_name": "Phenotype",
                "counter_id": "0",
            }),
        }),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    content = b"".join(response.streaming_content).decode()  # type: ignore
    rows = csv.DictReader(content.splitlines(), delimiter="\t")
    return {row["familyId"] for row in rows}


@pytest.mark.usefixtures("shared_family_instance")
def test_family_counter_download_of_the_merged_shared_family(
    admin_client: Client,
) -> None:
    assert _counter_download_families(admin_client) == {"fs"}


@pytest.mark.usefixtures("grant_on_study_b", "shared_family_instance")
def test_family_counter_download_leaves_out_a_partly_granted_family(
    user_client: Client,
) -> None:
    assert not _counter_download_families(user_client)


@pytest.mark.usefixtures(
    "grant_on_all_shared_studies", "shared_family_instance")
def test_grant_on_all_child_studies_shows_the_merged_family(
    user_client: Client,
) -> None:
    response = user_client.get("/api/v3/families/shared_dataset/fs/members")

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {  # type: ignore
        "mom", "dad", "ch_a", "ch_b", "ch_c",
    }
