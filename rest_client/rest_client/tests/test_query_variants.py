# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from rest_client.rest_client import RESTClient

QUERIES = [
    {
        "variantTypes": ["sub", "ins", "del"],
        "effectTypes": [
            "splice-site",
        ],
        "genders": ["male", "female", "unspecified"],
        "inheritanceTypeFilter": [],
        "presentInChild": ["proband only", "proband and sibling"],
        "studyTypes": ["we", "wg", "tg"],
        "familyIds": ["11111"],
        "genomicScores": [],
        "studyFilters": [],
        "uniqueFamilyVariants": False,
        "personSetCollection": {
            "id": "phenotype",
            "checkedValues": ["affected", "unaffected"],
        },
        "presentInParent": {
            "presentInParent": [
                "mother only",
                "father only",
                "mother and father",
                "neither",
            ],
            "rarity": {"ultraRare": False},
        },
        "datasetId": "iossifov_2014",
        "maxVariantsCount": 1001,
    },
]


def test_get_all_datasets(
    oauth_admin: RESTClient,
) -> None:
    """Get all datasets from the GPF API."""
    datasets = oauth_admin.get_all_datasets()
    assert datasets is not None
    assert len(datasets) > 0


def test_query_cancelation(
    oauth_admin: RESTClient,
) -> None:
    """Perform a variants query to the GPF API."""
    for chunk in oauth_admin.query_genotype_browser(QUERIES[0], 10):
        print(chunk)
        break


def test_query_variants_no_rights(
    user_client: RESTClient,
) -> None:
    """Perform a variants query to the GPF API."""

    with pytest.raises(
                OSError,
                match="Query failed:",
            ):
        user_client.query_genotype_browser(QUERIES[0], 10)
