# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Any, cast

import pytest
import pytest_mock
from datasets_api.partial_grants import get_granted_phenotype_data
from datasets_api.permissions import add_group_perm_to_user
from django.contrib.auth.models import User
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

from pheno_tool_api.adapter import PhenoToolAdapter, PhenoToolAdapterBase

PEOPLE_VALUES_URL = "/api/v3/pheno_tool/people_values"
MEASURE_URL = "/api/v3/pheno_tool/measure"
MEASURES_URL = "/api/v3/pheno_tool/measures"
INSTRUMENTS_URL = "/api/v3/pheno_tool/instruments"
DOWNLOAD_URL = "/api/v3/pheno_tool/download"
OTHER_LEAF_MEASURES = {"sib.age", "thr.score"}


def _people_values(
    client: Client, dataset_id: str, measure_ids: list[str],
) -> Any:
    return client.post(
        PEOPLE_VALUES_URL,
        json.dumps({"datasetId": dataset_id, "measureIds": measure_ids}),
        content_type="application/json",
    )


def _person_ids(response: Any) -> set[str]:
    table = json.loads(response.json())
    person_id = table["columns"].index("person_id")
    return {row[person_id] for row in table["data"]}


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_people_values_of_a_phenotype_group_under_partial_grant(
    user_client: Client,
) -> None:
    response = _people_values(user_client, "pheno_group", ["i1.age"])

    assert response.status_code == status.HTTP_200_OK
    assert _person_ids(response) == {
        f"{role}{index}"
        for role in ("mom", "dad", "p", "s") for index in range(1, 5)
    }


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_people_values_of_another_leaf_under_partial_grant_are_hidden(
    user_client: Client,
) -> None:
    response = _people_values(user_client, "pheno_group", ["sib.age"])

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b"px" not in response.content


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_measure_of_another_leaf_under_partial_grant_is_hidden(
    user_client: Client,
) -> None:
    response = user_client.get(
        f"{MEASURE_URL}?datasetId=pheno_group&measureId=sib.age")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_measures_of_a_phenotype_group_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get(f"{MEASURES_URL}?datasetId=pheno_group")

    assert response.status_code == status.HTTP_200_OK
    measure_ids = {m["measureId"] for m in response.json()}
    assert "i1.age" in measure_ids
    assert not measure_ids & OTHER_LEAF_MEASURES


@pytest.mark.usefixtures("grant_on_study_1_pheno", "pheno_group_instance")
def test_instruments_of_a_phenotype_group_under_partial_grant(
    user_client: Client,
) -> None:
    response = user_client.get(f"{INSTRUMENTS_URL}?datasetId=pheno_group")

    assert response.status_code == status.HTTP_200_OK
    assert "i1" in response.json()
    assert not set(response.json()) & {"sib", "thr"}


def _download(client: Client, measure_id: str) -> Any:
    query = {
        "datasetId": "pheno_parent",
        "measureId": measure_id,
        "normalizeBy": [],
        "effectTypes": ["missense"],
    }
    return client.post(
        DOWNLOAD_URL,
        json.dumps({"queryData": json.dumps(query)}),
        content_type="application/json",
    )


def _download_person_ids(response: Any) -> set[str]:
    assert response.status_code == status.HTTP_200_OK
    lines = b"".join(response.streaming_content).decode().splitlines()
    return {line.split(",")[0] for line in lines[1:]}


@pytest.mark.usefixtures("grant_on_t4c8_study_1")
def test_download_of_a_genotype_parent_under_partial_grant(
    user_client: Client,
    pheno_group_instance: WGPFInstance,
) -> None:
    parent = pheno_group_instance.get_wdae_wrapper("pheno_parent")
    assert parent is not None
    assert {"px", "py"} <= {
        person.person_id for person in parent.families.persons.values()}

    allowed = _download(user_client, "i1.m1")
    hidden = _download(user_client, "sib.age")

    assert _download_person_ids(allowed) == {"p1", "p3"}
    assert hidden.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("pheno_group_instance")
def test_download_of_a_genotype_parent_under_a_grant_on_the_parent(
    user: User,
    user_client: Client,
) -> None:
    add_group_perm_to_user("pheno_parent", user)

    assert _download_person_ids(_download(user_client, "sib.age")) == {"px"}
    assert _download_person_ids(_download(user_client, "thr.score")) == {
        "py"}


@pytest.mark.usefixtures("grant_on_t4c8_study_1", "pheno_group_instance")
def test_people_values_of_a_genotype_parent_under_partial_grant(
    user_client: Client,
) -> None:
    allowed = _people_values(user_client, "pheno_parent", ["i1.age"])
    hidden = _people_values(user_client, "pheno_parent", ["sib.age"])

    assert "p1" in _person_ids(allowed)
    assert hidden.status_code == status.HTTP_404_NOT_FOUND
    assert b"px" not in hidden.content


@pytest.mark.usefixtures("grant_on_t4c8_study_1", "pheno_group_instance")
def test_measure_routes_of_a_genotype_parent_under_partial_grant(
    user_client: Client,
) -> None:
    measure = user_client.get(
        f"{MEASURE_URL}?datasetId=pheno_parent&measureId=thr.score")
    measures = user_client.get(f"{MEASURES_URL}?datasetId=pheno_parent")
    instruments = user_client.get(f"{INSTRUMENTS_URL}?datasetId=pheno_parent")

    assert measure.status_code == status.HTTP_404_NOT_FOUND
    assert not {m["measureId"] for m in measures.json()} & OTHER_LEAF_MEASURES
    assert "i1" in instruments.json()
    assert not set(instruments.json()) & {"sib", "thr"}


@pytest.mark.parametrize("dataset_id", ["pheno_group", "pheno_parent"])
@pytest.mark.usefixtures("pheno_group_instance")
def test_pheno_tool_routes_under_a_grant_on_the_parent(
    user: User,
    user_client: Client,
    dataset_id: str,
) -> None:
    add_group_perm_to_user(dataset_id, user)

    people = _people_values(user_client, dataset_id, ["thr.score"])
    measure = user_client.get(
        f"{MEASURE_URL}?datasetId={dataset_id}&measureId=sib.age")
    measures = user_client.get(f"{MEASURES_URL}?datasetId={dataset_id}")
    instruments = user_client.get(f"{INSTRUMENTS_URL}?datasetId={dataset_id}")

    assert _person_ids(people) == {"momy", "dady", "py"}
    assert measure.status_code == status.HTTP_200_OK
    assert {m["measureId"] for m in measures.json()} >= OTHER_LEAF_MEASURES
    assert {"i1", "sib", "thr"} <= set(instruments.json())


@pytest.mark.parametrize(
    "filter_key", ["familyPhenoFilters", "personFiltersBeta"])
@pytest.mark.usefixtures("grant_on_t4c8_study_1", "pheno_group_instance")
def test_download_filter_on_a_measure_of_another_leaf_is_hidden(
    user_client: Client,
    filter_key: str,
) -> None:
    query = {
        "datasetId": "pheno_parent",
        "measureId": "i1.m1",
        "normalizeBy": [],
        "effectTypes": ["missense"],
        filter_key: [{
            "source": "sib.age",
            "histogramType": "continuous",
            "min": 0,
            "max": 100,
            "isFamily": True,
        }],
    }
    response = user_client.post(
        DOWNLOAD_URL,
        json.dumps({"queryData": json.dumps(query)}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("grant_on_t4c8_study_1", "pheno_group_instance")
def test_download_phenodb_family_filter_on_another_leaf_is_hidden(
    user_client: Client,
) -> None:
    query = {
        "datasetId": "pheno_parent",
        "measureId": "i1.m1",
        "normalizeBy": [],
        "effectTypes": ["missense"],
        "familyFilters": [{
            "from": "phenodb",
            "source": "sib.age",
            "sourceType": "continuous",
            "selection": {"min": 0, "max": 100},
            "role": "prb",
        }],
    }
    response = user_client.post(
        DOWNLOAD_URL,
        json.dumps({"queryData": json.dumps(query)}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("grant_on_t4c8_study_1")
def test_pheno_tool_adapter_reads_the_granted_phenotype_data(
    user: User,
    pheno_group_instance: WGPFInstance,
) -> None:
    parent = pheno_group_instance.get_wdae_wrapper("pheno_parent")
    assert parent is not None
    granted = get_granted_phenotype_data(pheno_group_instance, user, parent)

    adapter = cast(
        PhenoToolAdapter,
        pheno_group_instance.get_pheno_tool_adapter(parent, granted),
    )

    assert granted is not parent.phenotype_data
    assert adapter.pheno_tool.phenotype_data is granted
    assert adapter.helper.phenotype_data is granted


@pytest.mark.usefixtures("grant_on_t4c8_study_1")
def test_download_with_an_extension_adapter_under_partial_grant_is_403(
    user_client: Client,
    pheno_group_instance: WGPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:
    extension = mocker.Mock()
    adapter = mocker.Mock(spec=PhenoToolAdapterBase)
    adapter.produce_download.return_value = iter(())
    extension.get_tool.return_value = adapter
    mocker.patch.dict(pheno_group_instance.extensions, {"fake": extension})

    response = _download(user_client, "i1.m1")

    assert response.status_code == status.HTTP_403_FORBIDDEN
