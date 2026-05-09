# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest

from rest_client.rest_client import RESTClient, RESTError

QUERY = {
    "datasetId": "t4c8_study_1",
    "maxVariantsCount": 1001,
}


def test_get_all_datasets(
    oauth_admin: RESTClient,
) -> None:
    """Get all datasets from the GPF API."""
    datasets = oauth_admin.get_all_datasets()
    assert datasets is not None
    assert len(datasets) > 0


def test_query_collect_variants(
    oauth_admin: RESTClient,
) -> None:
    """Perform a variants query to the GPF API."""
    result = [
        chunk.decode("utf-8")
        for chunk in oauth_admin.query_genotype_browser(QUERY, 1000)
    ]
    assert result
    content = "".join(result)
    assert content
    result = json.loads(content)
    assert len(result) == 12


def test_query_cancelation(
    oauth_admin: RESTClient,
) -> None:
    """Perform a variants query to the GPF API."""
    for chunk in oauth_admin.query_genotype_browser(QUERY, 10):
        print(chunk)
        break


def test_query_variants_no_rights(
    user_client: RESTClient,
) -> None:
    """Perform a variants query to the GPF API."""

    with pytest.raises(
        RESTError,
        match="Query failed:",
    ):
        user_client.query_genotype_browser(QUERY, 10)


GENES = [
    "t4",
    "c8",
]

SUMMARY_QUERY = {
    "datasetId": "t4c8_study_1",
    "geneSymbols": GENES,
}


def test_query_summary_variants(
    oauth_admin: RESTClient,
) -> None:
    """Perform a variants query to the GPF API."""
    result = oauth_admin.query_summary_variants(SUMMARY_QUERY)
    assert len(result) == 4
